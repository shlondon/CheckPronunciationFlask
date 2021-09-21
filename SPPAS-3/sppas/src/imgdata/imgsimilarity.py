# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.imgsimilarity.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  An images clustering + recognition system

.. _This file is part of SPPAS: <http://www.sppas.org/>
..
    -------------------------------------------------------------------------

     ___   __    __    __    ___
    /     |  \  |  \  |  \  /              the automatic
    \__   |__/  |__/  |___| \__             annotation and
       \  |     |     |   |    \             analysis
    ___/  |     |     |   | ___/              of speech

    Copyright (C) 2011-2021  Brigitte Bigi
    Laboratoire Parole et Langage, Aix-en-Provence, France

    Use of this software is governed by the GNU Public License, version 3.

    SPPAS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SPPAS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SPPAS. If not, see <http://www.gnu.org/licenses/>.

    This banner notice must not be removed.

    -------------------------------------------------------------------------

"""

import os
import logging
import collections
import numpy
import cv2

from sppas.src.config import sppasTypeError
from sppas.src.config import sppasKeyError
from sppas.src.config import IntervalRangeException
from sppas.src.config import sppasTrash

from .coordinates import sppasCoords
from .image import sppasImage
from .imageutils import sppasImageCompare
from .imageutils import sppasCoordsCompare

# ---------------------------------------------------------------------------


class ImagesFIFO(object):
    """FIFO to store images and optionally two sppasCoords.

    """

    DEFAULT_QUEUE_SIZE = 20

    def __init__(self, size=DEFAULT_QUEUE_SIZE):
        """Create a new instance.

        :param size: (int) Size of the queue to store images
        :raise: TypeError

        """
        # Do not accept an inappropriate size of the queue
        size = int(size)
        if size < 0 or size > 50:
            logging.error("Error. A size between (0, 50) was expected but "
                          "got {:d}. Size is set ot its default {:d} value."
                          "".format(size, ImagesFIFO.DEFAULT_QUEUE_SIZE))
            size = ImagesFIFO.DEFAULT_QUEUE_SIZE

        # Set the size of the queue
        self.__limit = size

        # The list of images
        self.__img = list()

        # An image, supposed to be a reference one
        self.__ref = None

        # Coordinates in a parent image -- used if relevant
        self.__cur_coords = None    # lastly observed
        self.__ref_coords = None    # reference

    # -----------------------------------------------------------------------
    # Coordinates
    # -----------------------------------------------------------------------

    def get_cur_coords(self):
        """Return the lastly saved coords."""
        return self.__cur_coords

    # -----------------------------------------------------------------------

    def set_cur_coords(self, c):
        """Set the current coords."""
        if c is not None:
            if isinstance(c, sppasCoords) is False:
                raise sppasTypeError(c, "sppasCoords")
        self.__cur_coords = c

    # -----------------------------------------------------------------------

    def get_ref_coords(self):
        """Return the reference coords."""
        return self.__ref_coords

    # -----------------------------------------------------------------------

    def set_ref_coords(self, c):
        """Set the reference coords."""
        if c is not None:
            if isinstance(c, sppasCoords) is False:
                raise sppasTypeError(c, "sppasCoords")
        self.__ref_coords = c

    # -----------------------------------------------------------------------
    # Images of the kids
    # -----------------------------------------------------------------------

    def add(self, img, reference=False):
        """Add an image into the queue.

        :param img: (sppasImage)
        :param reference: (bool) This is the reference image
        :raise: TypeError

        """
        if isinstance(img, sppasImage) is False:
            raise sppasTypeError(img, "sppasImage")

        self.__img.append(img)
        if len(self.__img) > self.__limit:
            self.__img.pop(0)

        if reference is True or self.__ref is None:
            self.__ref = img.copy()

    # -----------------------------------------------------------------------

    def get_ref_image(self):
        """Return an image which is supposed to be THE reference.

        :return: (sppasImage or None)

        """
        return self.__ref

    # -----------------------------------------------------------------------
    # Overloads -- browse the list of images
    # -----------------------------------------------------------------------

    def __str__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    # ------------------------------------------------------------------------

    def __len__(self):
        """Return the number of images."""
        return len(self.__img)

    # ------------------------------------------------------------------------

    def __iter__(self):
        """Browse the current images."""
        for img in self.__img:
            yield img

    # ------------------------------------------------------------------------

    def __getitem__(self, item):
        if isinstance(item, sppasImage):
            return item in self.__img
        return False

    # -----------------------------------------------------------------------

    def __contains__(self, img):
        """Return true if img in images. """
        return img in self.__img

# ---------------------------------------------------------------------------


class sppasImagesSimilarity(object):
    """Estimate similarity between images to identify objects.

    This class store several sets of images and estimates similarity 
    measures to identify which, among the known sets, is represented 
    in a new image.
    
    Various solutions are implemented to estimate similarity:
        - the faster is to compare coordinates;
        - the slower is to compare image contents (colors, size, ...)
        - the most generic is to use the OpenCV recognition system.

    """

    def __init__(self):
        """Create an instance.

        """
        # Known objects: key=identifier, value=ImagesFIFO()
        self.__kids = collections.OrderedDict()

        # Members for the SPPAS similarity measures
        self.__score_level = 0.4

        # Members for OpenCV automatic recognizer
        self.__fr = False
        self.__recognizer = None

        # A number used to generate non-redundant identifiers
        self.__id_idx = 1

    # -----------------------------------------------------------------------
    # Known images and coords
    # -----------------------------------------------------------------------

    def get_known_identifiers(self):
        """Return the list of known identifiers."""
        return list(self.__kids.keys())

    # -----------------------------------------------------------------------

    def create_identifier(self, nb_img=ImagesFIFO.DEFAULT_QUEUE_SIZE):
        """Create a new identifier and add it in the list of known ones.

        :return: (str) new identifier name

        """
        pid = "id{:03d}".format(self.__id_idx)
        self.__kids[pid] = ImagesFIFO(nb_img)
        self.__id_idx += 1

        return pid

    # -----------------------------------------------------------------------

    def remove_identifier(self, kid):
        """Remove an identifier of the list of known ones.

        :param kid: (str) An identifier

        """
        if kid in self.__kids:
            del self.__kids[kid]

    # -----------------------------------------------------------------------

    def add_image(self, kid, image, reference=False):
        """Add an image to the known ones of the given identifier.

        :param kid: (str) An identifier
        :param image: (sppasImage)
        :param reference: (bool) This is the reference image for this kid
        :raise: KeyError, TypeError

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        self.__kids[kid].add(image, reference)

    # -----------------------------------------------------------------------

    def get_nb_images(self, kid):
        """Return the number of known images of the given identifier.

        :param kid: (str) An identifier
        :return: (int)

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        return len(self.__kids[kid])

    # -----------------------------------------------------------------------

    def get_ref_image(self, kid):
        """Return the reference image of the given identifier.

        :param kid: (str) An identifier
        :return: (sppasImage or None)

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        return self.__kids[kid].get_ref_image()

    # -----------------------------------------------------------------------

    def get_cur_coords(self, kid):
        """Return the current coordinates of an identifier or None if unknown.

        :param kid: (str) An identifier
        :raise: KeyError

        :return: (sppasCoords or None)

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        return self.__kids[kid].get_cur_coords()

    # -----------------------------------------------------------------------

    def set_cur_coords(self, kid, coords):
        """Set the current coordinates for an identifier.

        :param kid: (str) An identifier
        :param coords: (sppasCoords)
        :raise: KeyError, TypeError

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        self.__kids[kid].set_cur_coords(coords)

    # -----------------------------------------------------------------------

    def get_ref_coords(self, kid):
        """Return the reference coordinates of an identifier or None if unknown.

        :param kid: (str) An identifier
        :raise: KeyError

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        return self.__kids[kid].get_ref_coords()

    # -----------------------------------------------------------------------

    def set_ref_coords(self, kid, coords):
        """Set the reference coordinates of an identifier.

        :param kid: (str) An identifier
        :param coords: (sppasCoords)
        :raise: KeyError, TypeError

        """
        if kid not in self.__kids:
            raise sppasKeyError(kid, "dict(ImagesFIFO)")

        self.__kids[kid].set_ref_coords(coords)

    # -----------------------------------------------------------------------

    def enable_face_recognition(self, value=True):
        """Enable or disable the automatic recognizer.

        :param value: (bool)

        """
        self.__fr = bool(value)

    # -----------------------------------------------------------------------
    # Automatic identification: define similarity measures
    # -----------------------------------------------------------------------

    def set_score_level(self, value):
        """Fix threshold score for the identification measure.

        :param value: (float) Value in range [0., 1.]

        """
        value = float(value)
        if value < 0. or value > 1.:
            raise IntervalRangeException(value, 0, 1)

        self.__score_level = value

    # -----------------------------------------------------------------------

    def compare_kids_coords(self, kid1, kid2):
        """Return a similarity score between two known identifiers.

        :return: (float) Return 0. if no similarity or if eval not done

        """
        r1 = self.__kids[kid1].get_ref_coords()
        r2 = self.__kids[kid2].get_ref_coords()
        if r1 is not None and r2 is not None:
            cc = sppasCoordsCompare(r1, r2)
            ccr = cc.compare_coords()
        else:
            ccr = 0.

        l1 = self.__kids[kid1].get_cur_coords()
        l2 = self.__kids[kid2].get_cur_coords()
        if l1 is not None and l2 is not None:
            cc = sppasCoordsCompare(l1, l2)
            ccl = cc.compare_coords()
        else:
            ccl = 0.

        return (ccr+ccl) / 2.

    # -----------------------------------------------------------------------

    def identify(self, image=None, coords=None):
        """Among the known identifiers, who matches the given image/coords.

        Should return None if none of the known ids is recognized.

        :param image: (sppasImage)
        :param coords: (sppasCoords)
        :return: (kid, score) or (None, 0.)

        """
        kid = None
        score = 0.

        if len(self.__kids) > 0:
            # An image is given.
            if image is not None:
                # Priority is given to the OpenCV Recognition system
                if self.__recognizer is not None:
                    kid, score = self.predict_recognizer(image)
                if kid is None:
                    kid, score = self.predict_compare_images(image)

            # Coords are given
            if coords is not None:
                p, s = self.predict_compare_coords(coords)
                if kid is None:
                    kid = p
                    score = s
                else:
                    if p is not None:
                        # both image and coords are predicting the same
                        if kid == p:
                            score = max(score, s)
                        else:
                            # image and coords are predicting 2 different kids
                            if score > s:
                                score = score / 2.
                            else:
                                kid = p
                                score = s / 2.

        return kid, score

    # -----------------------------------------------------------------------
    # SPPAS similarity estimations
    # -----------------------------------------------------------------------

    def predict_compare_images(self, image):
        """Compare the given image to the existing ones.

        Evaluate similarity of image contents (very very low).

        :param image: (sppasImage) The image to compare with
        :return: tuple(kid, score) or (None, 0.)

        """
        scores = dict()
        for ref_name in self.__kids:
            sc = None
            ref_img = self.__kids[ref_name].get_ref_image()
            if ref_img is not None:
                cmp = sppasImageCompare(image, ref_img)
                areas = cmp.compare_areas()
                sizes = cmp.compare_sizes()
                mse = cmp.compare_with_mse()
                kld = cmp.compare_with_kld()
                scx = (0.4 * mse) + (0.3 * kld) + (0.15 * areas) + (0.15 * sizes)
                if sc is not None:
                    # we already used coords to have a score
                    sc = (sc+scx) / 2.
                else:
                    sc = scx

            if sc is None:
                sc = 0.
            scores[ref_name] = sc

        # choose the better score (or not!)
        # if at least one image have a good score
        scores = collections.Counter(scores)
        sorted_scores = scores.most_common()
        if sorted_scores[0][1] > self.__score_level:
            return sorted_scores[0]

        return None, 0.

    # -----------------------------------------------------------------------

    def predict_compare_coords(self, coords):
        """Compare the given coords to the existing ones.

        :param coords: (sppasCoords) The coords to compare with
        :return: tuple(kid, score) or (None, 0.)

        """
        scores = dict()
        for ref_name in self.__kids:
            ref_coords = self.__kids[ref_name].get_ref_coords()
            cur_coords = self.__kids[ref_name].get_cur_coords()
            sc1 = sc2 = None
            if ref_coords is not None:
                ccr = sppasCoordsCompare(ref_coords, coords)
                sc1 = ccr.compare_coords()
            if cur_coords is not None:
                ccr = sppasCoordsCompare(cur_coords, coords)
                sc2 = ccr.compare_coords()
            if sc1 is None or sc2 is None:
                if sc1 is None:
                    sc = sc2
                else:
                    sc = sc1
            else:
                sc = (0.4 * sc1) + (0.6 * sc2)

            if sc is None:
                sc = 0.
            scores[ref_name] = sc

        # choose the better score (or not!)
        # if at least one image have a good score
        scores = collections.Counter(scores)
        sorted_scores = scores.most_common()
        if sorted_scores[0][1] > self.__score_level:
            return sorted_scores[0]

        return None, 0.

    # -----------------------------------------------------------------------
    # OpenCV Face recognition integration
    # -----------------------------------------------------------------------

    def train_recognizer(self):
        """Train the recognizer from the current set of images of known ids.

        """
        images = list()
        labels = list()
        for i, kid in enumerate(self.__kids):
            for img in self.__kids[kid]:
                # Append the image converted to grayscale
                # and image width should be a multiple of 16
                gray = cv2.cvtColor(img.iresize(160, 160), cv2.COLOR_BGR2GRAY)
                images.append(gray)
                labels.append(i)

            img = self.__kids[kid].get_ref_image()
            gray = cv2.cvtColor(img.iresize(160, 160), cv2.COLOR_BGR2GRAY)
            images.append(gray)
            labels.append(len(images))

        self.__recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.__recognizer.train(images, numpy.array(labels))

    # -----------------------------------------------------------------------

    def predict_recognizer(self, image):
        """Compare the given image to the existing ones.

        :param image: (sppasImage)
        :return: tuple(kid, score) or (None, 0.)

        """
        if self.__recognizer is not None:
            gray_img = cv2.cvtColor(image.iresize(160, 160), cv2.COLOR_BGR2GRAY)
            kidx, dist = self.__recognizer.predict(gray_img)
            # dist=0 means the confidence is 100% i.e perfect match
            for i, kid in enumerate(self.__kids):
                if i == kidx:
                    confidence = 1. - float(dist) / 100.
                    if confidence < 0.:
                        # the dist was very far away...
                        return None, 0.
                    return kid, confidence

        return None, 0.

    # -----------------------------------------------------------------------
    # save data
    # -----------------------------------------------------------------------

    def write(self, folder):
        """Save the images of the known ids.

        :param folder: Place to save images

        """
        if os.path.exists(folder) is True:
            logging.warning("Folder {:s} is already existing. It is moved "
                            "into the Trash of SPPAS.".format(folder))
            sppasTrash().put_folder_into(folder)

        os.mkdir(folder)
        for kid in self.__kids:
            # Write images of the queue
            for i, image in enumerate(self.__kids[kid]):
                filename = "{:s}_{:02d}.png".format(kid, i)
                image.write(os.path.join(folder, filename))

            # Write the reference image
            img = self.__kids[kid].get_ref_image()
            filename = "{:s}_ref.png".format(kid)
            img.write(os.path.join(folder, filename))

    # -----------------------------------------------------------------------
    # Overloads -- Browse the dict of kids
    # -----------------------------------------------------------------------

    def __str__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    # ------------------------------------------------------------------------

    def __len__(self):
        """Return the number of kids."""
        return len(self.__kids)

    # ------------------------------------------------------------------------

    def __iter__(self):
        """Browse the current kids."""
        for kid in self.__kids:
            yield kid

    # ------------------------------------------------------------------------

    def __getitem__(self, item):
        """Return the ImagesFIFO() of a given kid. """
        if item not in self.__kids:
            raise sppasKeyError(item, "dict(ImagesFIFO)")

        return self.__kids[item]

    # -----------------------------------------------------------------------

    def __contains__(self, item):
        """Return true if item in kids. """
        return item in self.__kids
