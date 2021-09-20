# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.imgfacemark.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic detection of the 68 sights on the image of a face.

.. _This file is part of SPPAS: http://www.sppas.org/
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

OpenCV's facial landmark API is called Facemark. It has three different
implementations of landmark detection based on three different papers:

    - FacemarkKazemi: This implementation is based on a paper titled
    "One Millisecond Face Alignment with an Ensemble of Regression Trees"
     by V.Kazemi and J. Sullivan published in CVPR 2014.
    - FacemarkAAM: This implementation uses an Active Appearance Model
    and is based on an the paper titled "Optimization problems for fast
    AAM fitting in-the-wild" by G. Tzimiropoulos and M. Pantic, published
    in ICCV 2013.
    - FacemarkLBF: This implementation is based a paper titled "Face
    alignment at 3000 fps via regressing local binary features" by
    S. Ren published in CVPR 2014.

The fundamental concept is that any person will have 68 particular points
on the face (called sights).

"""

import logging
import cv2
import os
import numpy
import math

from sppas.src.exceptions import sppasIOError, IOExtensionError
from sppas.src.exceptions import sppasError, sppasTypeError
from sppas.src.imgdata import sppasImage

from .sights import Sights

# ---------------------------------------------------------------------------


ERR_MODEL_MISS = "At least a model must be loaded first."
ERR_NO_SIGHTS = "No sights detected in the face."

# ---------------------------------------------------------------------------


class ImageFaceLandmark(object):
    """Estimate the 68 sights on one face of an image.

    """

    def __init__(self):
        """Create a new FaceLandmark instance."""
        # The landmark recognizers -- at least one must be instantiated
        self.__markers = list()

        # The 68 sights detected on the face
        self.__sights = Sights(nb=68)

    # -----------------------------------------------------------------------

    def get_sights(self):
        """Return a copy of the sights."""
        return self.__sights.copy()

    # -----------------------------------------------------------------------

    def get_nb_recognizers(self):
        """Return the number of initialized landmark recognizers."""
        return len(self.__markers)

    # -----------------------------------------------------------------------

    def load_model(self, model_landmark, *args):
        """Initialize the face detection and recognizer from model files.

        :param model_landmark: (str) Filename of a recognizer model (Kazemi, LBF, AAM).
        :param args: (str) Other filenames of models for face landmark
        :raise: IOError, Exception

        """
        self.add_model(model_landmark)
        for f in args:
            try:
                self.add_model(f)
            except:
                pass

    # -----------------------------------------------------------------------

    def add_model(self, filename):
        """Append a recognizer into the list and load the model.

        :param filename: (str) A recognizer model (Kazemi, LBF, AAM).
        :raise: IOError, Exception

        """
        if os.path.exists(filename) is False:
            raise sppasIOError(filename)

        fn, fe = os.path.splitext(filename)
        fe = fe.lower()

        # Face landmark recognizer
        if fe == ".yaml":
            fm = cv2.face.createFacemarkLBF()
        elif fe == ".xml":
            fm = cv2.face.createFacemarkAAM()
        elif fe == ".dat":
            fm = cv2.face.createFacemarkKazemi()
        else:
            raise IOExtensionError(filename)

        try:
            fm.loadModel(filename)
            # TODO: check that the model is based on the detection of 68 sights but there's nothing in cv2 to do that...
            self.__markers.append(fm)
        except cv2.error as e:
            logging.error("Loading the model {} failed.".format(filename))
            raise sppasError(str(e))

    # -----------------------------------------------------------------------
    # Getters of specific points
    # -----------------------------------------------------------------------

    def get_chin(self):
        """Return coordinates of the right side of the face.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [10-16].

        """
        if len(self.__sights) == 68:
            return self.__sights[:17]
        return list()

    # -----------------------------------------------------------------------

    def get_left_eyebrow(self):
        """Return coordinates of the left brow.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [18-22].

        """
        if len(self.__sights) == 68:
            return self.__sights[17:22]
        return list()

    # -----------------------------------------------------------------------

    def get_right_eyebrow(self):
        """Return coordinates of the right brow.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [23-27].

        """
        if len(self.__sights) == 68:
            return self.__sights[22:27]
        return list()

    # -----------------------------------------------------------------------

    def get_nose(self):
        """Return coordinates of the nose.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [28-36].

        """
        if len(self.__sights) == 68:
            return self.__sights[27:36]
        return list()

    # -----------------------------------------------------------------------

    def get_left_eye(self):
        """Return coordinates of the left eye.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [37-42].

        """
        if len(self.__sights) == 68:
            return self.__sights[36:42]
        return list()

    # -----------------------------------------------------------------------

    def get_right_eye(self):
        """Return coordinates of the right eye.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [43-48].

        """
        if len(self.__sights) == 68:
            return self.__sights[42-48]
        return list()

    # -----------------------------------------------------------------------

    def get_lips(self):
        """Return coordinates of the mouth.

        If the list of marked points has the 68-standard number of points that
        make up an "Active Shape Model", return points [49-68].

        """
        if len(self.__sights) == 68:
            return self.__sights[48:]
        return list()

    # -----------------------------------------------------------------------
    # Automatic detection of the landmark points
    # -----------------------------------------------------------------------

    def invalidate(self):
        """Invalidate current list of sight coordinates."""
        self.__sights = Sights(nb=68)

    # -----------------------------------------------------------------------

    def detect_sights(self, image, coords):
        """Detect sights on an image with the coords of the face.

        Sights are internally stored. Get access with an iterator or getters.

        :param image: (sppasImage or numpy.ndarray) The image to be processed.
        :param coords: (sppasCoords) Coordinates of the face in the image

        """
        self.__sights = Sights(nb=68)
        if len(self.__markers) == 0:
            raise sppasError(ERR_MODEL_MISS)

        # Convert image to sppasImage if necessary
        if isinstance(image, numpy.ndarray) is True:
            image = sppasImage(input_array=image)
        if isinstance(image, sppasImage) is False:
            raise sppasTypeError("image", "sppasImage")

        shift_x, shift_y = coords.scale(1.)
        coords.shift(shift_x, shift_y)

        # Estimate all the 68 points by each instantiated face-marker
        all_points = self.__detect_with_markers(image, coords)
        if len(all_points[0]) == 0:
            raise sppasError(ERR_NO_SIGHTS)

        # Add the empirically fixed sights, they are used to smooth...
        empirical = ImageFaceLandmark.basic_sights(image, coords)
        for i, c in enumerate(empirical):
            (x, y, score) = c
            all_points[i].append((x, y))

        # Interpolate all the points and store into our landmarks
        for i in range(len(self.__sights)):
            x, y, score = self.points_to_coords(image, coords, all_points[i])
            self.__sights.set_sight(i, x, y, score)

    # ------------------------------------------------------------------------

    @staticmethod
    def basic_sights(image, coords):
        """Return empirically fixed sights which does not require any model.

        All sights were estimated by supposing that:
            1. it's a frontal face
            2. coords are properly surrounding the face

        :param image: (numpy.ndarray) The image to be processed.
        :param coords: (sppasCoords) Coordinates of the face in the image.
        :return: (Sights) Estimated sights.

        """
        basic_sights = Sights(nb=68)
        img = image.icrop(coords)
        h, w = img.shape[:2]
        sx = w // 20
        sy = h // 20
        x = w // 2
        y = h // 2

        # chin -- face contour
        basic_sights.set_sight(0, 1, y - (2*sy))
        basic_sights.set_sight(1, sx // 3, y)
        basic_sights.set_sight(2, sx // 2, y + (2*sy))
        basic_sights.set_sight(3, sx, y + (4*sy))
        basic_sights.set_sight(4, 2*sx, y + (6*sy))
        basic_sights.set_sight(5, 4*sx, y + (8*sy))
        basic_sights.set_sight(6, 6*sx, h - sy)
        basic_sights.set_sight(7, 8*sx, h - (sy//2))
        basic_sights.set_sight(8, x, h)
        basic_sights.set_sight(9, x + (2*sx), h - (sy//2))
        basic_sights.set_sight(10, x + (4*sx), h - sy)
        basic_sights.set_sight(11, x + (6*sx), y + (8*sy))
        basic_sights.set_sight(12, x + (8*sx), y + (6*sy))
        basic_sights.set_sight(13, w - sx, y + (4*sy))
        basic_sights.set_sight(14, w - (sx // 2), y + (2*sy))
        basic_sights.set_sight(15, w - (sx // 3), y)
        basic_sights.set_sight(16, w - 1, y - (2*sy))

        # brows
        basic_sights.set_sight(17, 2*sx, 6*sy)
        basic_sights.set_sight(18, (3*sx) + (sx//2), (5*sy) + (sy//2))
        basic_sights.set_sight(19, 5*sx, 5*sy)
        basic_sights.set_sight(20, (6*sx) + (sx//2), (5*sy) + (sy//2))
        basic_sights.set_sight(21, 8*sx, 6*sy)
        basic_sights.set_sight(22, x + 2*sx, 6*sy)
        basic_sights.set_sight(23, x + (3*sx) + (sx//2), (5*sy) + (sy//2))
        basic_sights.set_sight(24, x + 5*sx, 5*sy)
        basic_sights.set_sight(25, x + (6*sx) + (sx//2), (5*sy) + (sy//2))
        basic_sights.set_sight(26, x + (8*sx), 6*sy)

        # nose
        basic_sights.set_sight(27, x, y - (2*sy) - (sy//2))
        basic_sights.set_sight(28, x, y - sy - (sy//2))
        basic_sights.set_sight(29, x, y - (sy//2))
        basic_sights.set_sight(30, x, y + (sy//2))
        basic_sights.set_sight(31, x - (3*sx), y + (2*sy) - (sy//2))
        basic_sights.set_sight(32, x - (2*sx), y + (2*sy) - (sy//3))
        basic_sights.set_sight(33, x, y + (2*sy))
        basic_sights.set_sight(34, x + (2*sx), y + (2*sy) - (sy//3))
        basic_sights.set_sight(35, x + (3*sx), y + (2*sy) - (sy//2))

        # eyes
        basic_sights.set_sight(36, x - (6*sx), 7*sy + (sy//2))
        basic_sights.set_sight(37, x - (5*sx) - (sx//4), 7*sy)
        basic_sights.set_sight(38, x - (4*sx), 7*sy)
        basic_sights.set_sight(39, x - (3*sx), 7*sy + (sy//2))
        basic_sights.set_sight(40, x - (4*sx), 8*sy)
        basic_sights.set_sight(41, x - (5*sx), 8*sy)
        basic_sights.set_sight(42, x + (3*sx), 7*sy + (sy//2))
        basic_sights.set_sight(43, x + (4*sx), 7*sy)
        basic_sights.set_sight(44, x + (5*sx), 7*sy)
        basic_sights.set_sight(45, x + (6*sx), 7*sy + (sy//2))
        basic_sights.set_sight(46, x + (5*sx), 8*sy)
        basic_sights.set_sight(47, x + (4*sx), 8*sy)

        # mouth
        basic_sights.set_sight(48, x - (4*sx), y + (4*sy) + (sy//2))
        basic_sights.set_sight(49, x - (2*sx) - (sx//2), y + (4*sy))
        basic_sights.set_sight(50, x - sx, y + (4*sy) - (sy//3))
        basic_sights.set_sight(51, x, y + (4*sy) - (sy//4))
        basic_sights.set_sight(52, x + sx, y + (4*sy) - (sy//3))
        basic_sights.set_sight(53, x + (2*sx) + (sx//2), y + (4*sy))
        basic_sights.set_sight(54, x + (4*sx), y + (4*sy) + (sy//2))
        basic_sights.set_sight(55, x + (2*sx) + (sx//2), y + (5*sy) + (sy//4))
        basic_sights.set_sight(56, x + sx, y + (6*sy) - (sy//4))
        basic_sights.set_sight(57, x, y + (6*sy))
        basic_sights.set_sight(58, x - sx, y + (6*sy) - (sy//4))
        basic_sights.set_sight(59, x - (2*sx) - (sx//2), y + (5*sy) + (sy//4))
        basic_sights.set_sight(60, x - (2*sx) - (sx//2), y + (4*sy) + (sy//2))
        basic_sights.set_sight(61, x - sx, y + (4*sy) + (sy//4))
        basic_sights.set_sight(62, x, y + (4*sy) + (sy//2))
        basic_sights.set_sight(63, x + sx, y + (4*sy) + (sy//4))
        basic_sights.set_sight(64, x + (2*sx) + (sx//2), y + (4*sy) + (sy//2))
        basic_sights.set_sight(65, x + sx, y + (5*sy))
        basic_sights.set_sight(66, x, y + (5*sy) + (sy//4))
        basic_sights.set_sight(67, x - sx, y + (5*sy))

        # adjust to the image coords and not the face ones
        for i, s in enumerate(basic_sights):
            x, y, score = s
            x += coords.x
            y += coords.y
            basic_sights.set_sight(i, x, y)

        return basic_sights

    # ------------------------------------------------------------------------

    def points_to_coords(self, image, coords, points):
        """Convert a list of estimated points into coordinates of a sight.

        The confidence score of each sight depends on the area covered by the
        points.

        :param image: (numpy.ndarray) The image to be processed.
        :param coords: (sppasCoords) Coordinates of the face in the image.
        :param points: (list of (x,y) values) A sight detected by each method
        :return: (sppasCoord) Estimated (x,y) values and confidence score.

        """
        # Get width and height of the face
        img = image.icrop(coords)
        h, w = img.shape[:2]

        # The area of the face
        face_area = h * w
        # The number of points
        nb_points = len(points)
        expected = len(self.__markers) + 1
        if nb_points != expected:
            raise Exception("Expected {:d} points, got {}".format(expected, nb_points))

        # Get the area of points detected by each method
        sum_x = sum(result[0] for result in points)
        sum_y = sum(result[1] for result in points)
        min_x = min(result[0] for result in points)
        min_y = min(result[1] for result in points)
        max_x = max(result[0] for result in points)
        max_y = max(result[1] for result in points)
        points_area = (max_x - min_x) * (max_y - min_y)

        # Fix the score -- the larger the area the worse
        ratio = float(points_area) / float(face_area)
        coeff = max(1., min(5., 100. * ratio))
        score = min(1., max(0., 1. - (coeff * ratio)))

        # Fix (x,y) in the middle
        x = round(float(sum_x) / float(len(points)))
        y = round(float(sum_y) / float(len(points)))

        return x, y, score

    # ------------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------------

    def __detect_with_markers(self, image, coords):
        """Estimate all the 68 points by each instantiated face-marker.

        The returned result is a list of 68 lists of tuples with (x,y) values
        because it's the data structure OpenCV is returning when invoking
        the method 'fit()' of each recognizer.

        """
        # The face-markers require the face coordinates in a numpy array
        rects = numpy.array([[coords.x, coords.y, coords.w, coords.h]],
                            dtype=numpy.int32)
        # The result is a list of 68 lists of tuples with (x,y) values.
        all_points = {i:list() for i in range(len(self.__sights))}

        # For each instantiated OpenCV FaceSights
        # https://docs.opencv.org/trunk/db/dd8/classcv_1_1face_1_1Facemark.html
        for face_marker in self.__markers:
            try:
                # Detect facial landmarks from the image with the face-marker
                marked, landmarks = face_marker.fit(image, rects)
                # Get the 68 lists of numpy arrays with (x,y) values
                points = landmarks[0][0]
                if marked is True:
                    if len(points) != len(self.__sights):
                        raise sppasError(
                            "Normally, {} sights should be detected. "
                            "Got {} instead.".format(len(self.__sights), len(points)))

                    # Convert the list of numpy arrays into a list of tuples
                    for i in range(len(self.__sights)):
                        (x, y) = points[i]
                        all_points[i].append((round(x), round(y)))

            except cv2.error as e:
                logging.error("Landmark detection failed with error: "
                              "{}".format(str(e)))
            except sppasError as e:
                logging.error(str(e))

        return all_points

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __len__(self):
        """Return the number of landmarks."""
        return len(self.__sights)

    # -----------------------------------------------------------------------

    def __iter__(self):
        for i in range(len(self.__sights)):
            yield self.__sights[i]

    # ----------------------------------------------------------------------

    def __getitem__(self, i):
        return self.__sights[i]

    # ----------------------------------------------------------------------

    def __contains__(self, other):
        """Return true if value in sights -- score is ignored.

        :param other: a list/tuple of (x,y,score)

        """
        return other in self.__sights

    # -----------------------------------------------------------------------

    def __str__(self):
        """Return coords separated by CR."""
        return "\n".join([str(coords) for coords in self.__sights])

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)
