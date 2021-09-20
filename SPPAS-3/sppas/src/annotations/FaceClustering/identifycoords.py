# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.identifycoords.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Cluster and identify the sets of coords of a video.

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

import logging
import collections
import os

from sppas.src.exceptions import sppasError
from sppas.src.calculus import symbols_to_items
from sppas.src.calculus import tansey_linear_regression
from sppas.src.calculus import linear_fct
from sppas.src.calculus import linear_values
from sppas.src.calculus import fmean
from sppas.src.imgdata import sppasCoords
from sppas.src.imgdata import sppasCoordsCompare
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import sppasImagesSimilarity

from sppas.src.annotations.FaceDetection import ImageFaceDetection

from .kidsbuffer import sppasKidsVideoBuffer
from .kidswriter import sppasKidsVideoReader
from .kidswriter import sppasKidsVideoWriter

# ---------------------------------------------------------------------------

MSG_ERROR_MISMATCH = "The given {:d} coordinates in CSV file doesn't match " \
                     "the number of frames of the video {:d}"

# ---------------------------------------------------------------------------


class VideoCoordsIdentification(object):
    """Set an identity to the coordinates detected in a video.

    """

    def __init__(self):
        """Create a new instance.

        """
        # Video stream with a buffer of images and the lists of coordinates
        self._video_buffer = sppasKidsVideoBuffer()

        # Threshold applied to the confidence score in order to determinate 
        # if it's a kid candidate.
        self.__minconf = 0.90

        # Number of images in the ImagesFIFO() to train the recognition system
        self.__nb_fr_img = 20

        # Kids data & similarity measures: identifier, images, coords...
        self.__kidsim = sppasImagesSimilarity()

        # Export a video file for each identified person
        self._out_ident = True

    # -----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    def set_out_ident(self, value):
        """Export a video/csv file for each identified person."""
        self._out_ident = bool(value)

    # -----------------------------------------------------------------------

    def set_ident_min_confidence(self, value):
        """Fix the minimum confidence score to propose a coord as candidate.

        :param value: (float) threshold for the confidence score of coords

        """
        if value < 0. or value > 1.:
            raise ValueError
        self.__minconf = float(value)

    # -----------------------------------------------------------------------

    def invalidate(self):
        """Invalidate the list of all known identifiers."""
        self.__kidsim = sppasImagesSimilarity()

    # -----------------------------------------------------------------------
    # Assign an identity to detected coordinates
    # -----------------------------------------------------------------------

    def video_identity(self, video, csv_coords, video_writer=None, output=None, pattern="-ident"):
        """Browse the video, get coords then cluster, identify and write results.

        :param video: (str) Video filename
        :param csv_coords: (str) Filename with the coords
        :param video_writer: (sppasKidsVideoWriter)
        :param output: (str) The output name for the folder
        :param pattern: (str) Optional output pattern

        :return: (list)

        """
        self.invalidate()
        # Open the video stream
        self._video_buffer.open(video)
        if video_writer is not None:
            video_writer.set_fps(self._video_buffer.get_framerate())

        # Load the coordinates from the CSV file
        br = sppasKidsVideoReader(csv_coords)
        coords = br.coords
        nframes = self._video_buffer.get_nframes()
        if len(coords) != nframes:
            # Release the video stream
            self._video_buffer.close()
            self._video_buffer.reset()
            raise sppasError(MSG_ERROR_MISMATCH.format(len(coords), nframes))

        # Cluster coords into kids and remove duplicated kids
        self.__first_pass_clustering(coords)
        self.__filter_kids()
        if output is not None:
            # write the stored images of each kid in the output folder
            self.__kidsim.write(output)

        # Associate each coord to a kid or remove it if no kid matches
        self.__kidsim.train_recognizer()
        coords, idents = self.__second_pass_identification(coords)

        # Smooth coordinates and save into video/csv/image files
        # result is the list of created file names
        result = self.__third_pass_smoothing(coords, idents, video_writer, output, pattern)

        # Release the video stream
        self._video_buffer.close()
        self._video_buffer.reset()

        if output is not None and video_writer is not None:
            return result

        return self.__kidsim.get_known_identifiers()

    # -----------------------------------------------------------------------

    def __first_pass_clustering(self, coords):
        """Create the kids in the whole video.

        :param coords: (list of list of sppasCoords)

        """
        logging.info("System 1st pass: Cluster coordinates to create "
                     "the set of known identities.")

        # Browse the video using the buffer of images
        read_next = True
        i = 0
        nb = 0
        self._video_buffer.seek_buffer(0)

        while read_next is True:
            # fill-in the buffer with 'size'-images of the video
            logging.info(" ... buffer number {:d}".format(nb+1))
            read_next = self._video_buffer.next()

            # fill-in the buffer with coords
            for buf_idx, image in enumerate(self._video_buffer):
                all_idx_coords = coords[i+buf_idx]
                self._video_buffer.set_coordinates(buf_idx, all_idx_coords)

            # cluster the coords to set the identities
            self.__cluster_buffer()

            nb += 1
            i += len(self._video_buffer)

        logging.info(" ... {:d} identities were found.".format(len(self.__kidsim)))

    # -----------------------------------------------------------------------

    def __filter_kids(self):
        """Verify if all kids are different ones and remove duplicated.
        
        """
        dist = dict()
        remove_ids = list()
        for pid1 in self.__kidsim:
            for pid2 in self.__kidsim:
                if pid1 == pid2:
                    continue
                if (pid1, pid2) not in dist and (pid2, pid1) not in dist:
                    score_coords = self.__kidsim.compare_kids_coords(pid1, pid2)
                    dist[(pid1, pid2)] = score_coords
                    if score_coords > 0.1:
                        # The coordinates are overlapping
                        # Do we have also to compare image contents to confirm?????????
                        nb1 = self.__kidsim.get_nb_images(pid1)
                        nb2 = self.__kidsim.get_nb_images(pid2)
                        if nb1 >= nb2 and pid2 not in remove_ids:
                            remove_ids.append(pid2)
                            logging.info(" ... identity {:s} is removed because "
                                         "duplicated with {:s}".format(pid2, pid1))
                        if nb2 > nb1 and pid1 not in remove_ids:
                            remove_ids.append(pid1)
                            logging.info(" ... identity {:s} is removed because "
                                         "duplicated with {:s}".format(pid1, pid2))

        for pid in remove_ids:
            self.__kidsim.remove_identifier(pid)

    # -----------------------------------------------------------------------

    def __second_pass_identification(self, coords):
        """Set an identity to the coords in the whole video.

        :param coords: (list of list of sppasCoords)
        :param video_writer: (sppasKidsVideoWriter)
        :param output: (str) The output name for the folder

        """
        logging.info("System 2nd pass: assign each coordinate an identity or "
                     "remove it.")

        # Browse the video using the buffer of images
        read_next = True
        idents = list()
        revised_coords = list()
        i = 0
        nb = 0
        self._video_buffer.seek_buffer(0)
        while read_next is True:
            # fill-in the buffer with 'size'-images of the video
            logging.info(" ... buffer number {:d}".format(nb+1))
            read_next = self._video_buffer.next()

            # fill-in the buffer with coords
            for buf_idx, image in enumerate(self._video_buffer):
                self._video_buffer.set_coordinates(buf_idx, coords[i + buf_idx])

            # set identity to coords of the buffer
            self.__identify_buffer()
            for buf_idx, image in enumerate(self._video_buffer):
                all_coords = self._video_buffer.get_coordinates(buf_idx)
                all_ids = self._video_buffer.get_ids(buf_idx)
                idents.append(all_ids)
                revised_coords.append(all_coords)

            nb += 1
            i += len(self._video_buffer)

        assert len(coords) == len(revised_coords)
        return revised_coords, idents

    # -----------------------------------------------------------------------

    def __third_pass_smoothing(self, coords, idents, video_writer, output, pattern):
        """Smooth and save coords of the persons in the the whole video."""
        logging.info("System 3rd pass: Smooth and save the identified persons")

        prev_coords = None  # the coords in the last image of the previous buffer
        prev_ids = None     # the ids in the last image of the previous buffer
        read_next = True    # reached the end of the video or not
        i = 0               # index of the first image of each buffer
        nb = 0              # buffer number
        result = list()
        self._video_buffer.seek_buffer(0)
        self._video_buffer.set_buffer_size(int(2. * video_writer.get_fps()))
        kids_video_writers, kids_video_buffers = self.create_kids_writers_buffers(video_writer)

        while read_next is True:
            # fill-in the buffer with 'size'-images of the video
            if nb % 10 == 0:
                logging.info(" ... buffer number {:d}".format(nb + 1))

            # fill-in the buffer with images, coords and ids
            read_next = self._video_buffer.next()
            for buf_idx, image in enumerate(self._video_buffer):
                self._video_buffer.set_coordinates(buf_idx, coords[i + buf_idx])
                self._video_buffer.set_ids(buf_idx, idents[i + buf_idx])

            # set person identity to faces of the buffer
            self.__smooth_buffer(prev_coords, prev_ids)

            # save the current results: created file names
            if output is not None:
                if video_writer is not None:
                    new_files = video_writer.write(self._video_buffer, output, pattern)
                    result.extend(new_files)
                    if self._out_ident is True:
                        for kid in self.__kidsim:
                            new_files = self.__export_kid(output, kid, kids_video_buffers[kid], kids_video_writers[kid])
                            result.extend(new_files)

            # prepare next buffer
            prev_coords = self._video_buffer.get_coordinates(len(self._video_buffer)-1)
            prev_ids = self._video_buffer.get_ids(len(self._video_buffer)-1)
            nb += 1
            i += len(self._video_buffer)

        return result

    # -----------------------------------------------------------------------

    @staticmethod
    def __coords_to_portrait(coords, image):
        """Return a list of coordinates to their portrait size."""
        portraits = list()
        for coord in coords:
            c = ImageFaceDetection.eval_portrait(coord, image)
            portraits.append(c)
        return portraits

    # -----------------------------------------------------------------------

    def __cluster_buffer(self):
        """Search for kids among the given coords: system 1st pass.
        
        """
        self.__kidsim.set_score_level(0.4)

        # Browse the buffer to search for new identifiers.
        for i in range(len(self._video_buffer)):
            image = self._video_buffer[i]
            coords_i = self._video_buffer.get_coordinates(i)

            for f, c in enumerate(coords_i):
                # The coord has a high enough confidence -- so supposed relevant 
                if c.get_confidence() > self.__minconf:
                    # Already an identified kid or a new one?
                    # Try to identify the kid with the coordinates
                    identity, score = self.__kidsim.identify(image=None, coords=c)
                    if identity is None:
                        # The coords are not matching a kid. So, this is probably a new one.
                        kid = self.__create_kid(i, f)
                    else:
                        # The coords are matching a kid.
                        if score > 0.6 and self.__kidsim.get_nb_images(identity) < self.__nb_fr_img:
                            cropped_img = image.icrop(c)
                            self.__kidsim.add_image(identity, cropped_img, reference=False)
                        # update coords to follow when the kid is moving
                        self.__kidsim.set_cur_coords(identity, c)

    # -----------------------------------------------------------------------

    def __identify_buffer(self):
        """Set an identifier to coords and apply filters: system 2nd pass.

        """
        # Assign an identity to coordinates
        self.__kidsim.set_score_level(0.4)
        self._set_identity_by_similarity()

        # Remove un-relevant isolates detected coords and
        # fill in holes of relevant missing ones
        for kid in self.__kidsim:
            self._dissociate_or_fill_isolated(kid)

        # Use rules to remove un-relevant detected kids
        self._dissociate_rare_and_scattered()

        # Remove the un-identified coords in each image of the buffer
        for i in range(len(self._video_buffer)):
            # Get detected identifiers in this image
            all_ids = self._video_buffer.get_ids(i)
            c = len(all_ids) - 1
            for kid in reversed(all_ids):
                if kid.startswith("unk"):
                    self._video_buffer.pop_coordinate(i, c)
                c -= 1

    # -----------------------------------------------------------------------

    def __smooth_buffer(self, last_coords=None, last_ids=None):
        """Smooth the coords of detected persons.

        :param last_coords: (sppasCoords) The previous coords before this buffer
        :param last_ids: (sppasCoords) The previous ids before this buffer

        """
        if last_coords is None or last_ids is None:
            last_coords = None
            last_ids = None

        for kid_id in self.__kidsim:
            # fix the last coord of this kid in the previous buffer
            last_coord = None
            if last_ids is not None and kid_id in last_ids:
                kid_idx = last_ids.index(kid_id)
                last_coord = last_coords[kid_idx]

            # create the list of points with all known coordinates of the kid
            px = list()
            py = list()
            pw = list()
            ph = list()
            for img_idx in range(len(self._video_buffer)):
                all_coords = self._video_buffer.get_coordinates(img_idx)
                all_ids = self._video_buffer.get_ids(img_idx)

                if kid_id in all_ids:
                    kid_idx = all_ids.index(kid_id)
                    c = all_coords[kid_idx]
                    if c is not None:
                        px.append((img_idx, c.x))
                        py.append((img_idx, c.y))
                        pw.append(c.w)
                        ph.append(c.h)

            # linear regression to fix the equation of the line representing
            # as close as possible the (x,y) coords of the kid.
            wm = int(fmean(pw))
            hm = int(fmean(ph))
            if len(px) > 2:
                bx, ax = tansey_linear_regression(px)
                by, ay = tansey_linear_regression(py)
                start = 0
                dest = (0, 0)
                if last_coord is not None:
                    start = min(10, len(self._video_buffer) // 4)
                # Set the new coords to the kid
                for img_idx in range(start, len(self._video_buffer)):
                    all_coords = self._video_buffer.get_coordinates(img_idx)
                    all_ids = self._video_buffer.get_ids(img_idx)
                    x = int(linear_fct(img_idx, ax, bx))
                    y = int(linear_fct(img_idx, ay, by))
                    if img_idx == start:
                        dest = (x, y)
                    if kid_id in all_ids:
                        kid_idx = all_ids.index(kid_id)
                        c = all_coords[kid_idx]
                        if c is not None:
                            c.x = x
                            c.y = y
                            c.w = wm
                            c.h = hm
                    else:
                        c = sppasCoords(x, y, wm, hm, 0.)
                        ci = self._video_buffer.append_coordinate(img_idx, c)
                        self._video_buffer.set_id(img_idx, ci, kid_id)
                        logging.debug("Added coords {} for {} at {}".format(c, kid_id, img_idx))

                # transition period
                # smooth with the last coord of the previous buffer
                if last_coord is not None and start > 0:
                    delta_x = float(dest[0] - last_coord.x) / float(start+1)
                    delta_w = float(wm - last_coord.w) / float(start+1)
                    if delta_x > 0.2 or delta_x < -0.2:
                        y_positions = linear_values(delta_x, (last_coord.x, last_coord.y), dest)
                    else:
                        y_positions = [last_coord.y]*(start+1)
                    if delta_w > 0.2 or delta_w < -0.2:
                        h_sizes = linear_values(delta_w, (last_coord.w, last_coord.h), (wm, hm))
                    else:
                        h_sizes = [last_coord.h]*(start+1)

                    for img_idx in range(start):
                        all_coords = self._video_buffer.get_coordinates(img_idx)
                        all_ids = self._video_buffer.get_ids(img_idx)
                        if kid_id in all_ids:
                            kid_idx = all_ids.index(kid_id)
                            x = last_coord.x + int((img_idx+1)*delta_x)
                            y = int(y_positions[img_idx+1])
                            w = last_coord.w + int((img_idx+1)*delta_w)
                            h = int(h_sizes[img_idx+1])

                            current_c = all_coords[kid_idx]
                            if current_c is not None:
                                c = sppasCoords(x, y, int(w), int(h), current_c.get_confidence())
                                self._video_buffer.set_coordinate(img_idx, all_coords.index(current_c), c)
                            else:
                                c = sppasCoords(x, y, int(w), int(h), 0.)
                                ci = self._video_buffer.append_coordinate(img_idx, c)
                                self._video_buffer.set_id(img_idx, ci, kid_id)
                                logging.debug("Added coords {} for {} at {}".format(c, kid_id, img_idx))

    # -----------------------------------------------------------------------

    def __export_kid(self, output, kid, kid_buffer, kid_writer):
        """Export the buffer into video/csv of each kid."""
        w = 640
        h = 480

        kid_buffer.reset()
        # Fill in the kids buffer with the cropped images
        for img_idx in range(len(self._video_buffer)):
            image = self._video_buffer[img_idx]
            all_coords = self._video_buffer.get_coordinates(img_idx)
            portraits = self.__coords_to_portrait(all_coords, image)
            all_ids = self._video_buffer.get_ids(img_idx)
            if kid in all_ids:
                kid_idx = all_ids.index(kid)
                cropped = image.icrop(portraits[kid_idx])
                kid_img = cropped.iextend(w, h)
            else:
                kid_img = sppasImage(0).blank_image(w, h)
            kid_buffer.append(kid_img)
            kid_buffer.set_coordinates(img_idx, all_coords)
            kid_buffer.set_ids(img_idx, all_ids)

        # Save to video/csv/img files
        pathname = os.path.dirname(output)
        filename = kid + "_" + os.path.basename(output)
        new_files = kid_writer.write(kid_buffer, os.path.join(pathname, filename))

        return new_files

    # -----------------------------------------------------------------------

    def create_kids_writers_buffers(self, video_writer):
        """Create as many kids writers&buffers as the number of persons."""
        kids_video_writers = dict()
        kids_video_buffers = dict()
        if video_writer is not None:
            w = video_writer.get_output_width()
            h = video_writer.get_output_height()
            for kid_id in self.__kidsim:
                writer = sppasKidsVideoWriter()
                writer.set_fps(video_writer.get_fps())
                writer.set_image_extension(video_writer.get_image_extension())
                writer.set_video_extension(video_writer.get_video_extension())
                writer.set_options(csv=False, folder=False, tag=False, crop=False, width=w, height=h)
                writer.set_video_output(True)
                kids_video_writers[kid_id] = writer
                kids_video_buffers[kid_id] = sppasKidsVideoBuffer(size=self._video_buffer.get_buffer_size())
        return kids_video_writers, kids_video_buffers

    # -----------------------------------------------------------------------

    def _dissociate_or_fill_isolated(self, kid):
        """Remove the coordinates of a kid in an isolated image.

        When a kid is detected at an image i-1 but not at both
        image i and image i-2, cancel its link to the coordinates.

        A kid can't appear furtively nor disappear!!!

        """
        here = [False, False, False]

        # For each image of the buffer
        for i in range(len(self._video_buffer)):
            # Get detected identifiers in this image
            all_ids = self._video_buffer.get_ids(i)
            if kid in all_ids:
                # the kid is detected at i and i-2 but wasn't at i-1
                here[2] = True
                if i > 1 and here[0] is True and here[1] is False:
                    # check if there wasn't a detection/identification problem
                    coord_prev = self._video_buffer.get_id_coordinate(i-2, kid)
                    coord_cur = self._video_buffer.get_id_coordinate(i, kid)
                    cc = sppasCoordsCompare(coord_prev, coord_cur)
                    # at i-1 and at i, it's seems it's really the same kid
                    if cc.compare_coords() > 0.5:
                        # add the kid at i-1
                        c = coord_prev.intermediate(coord_cur)
                        nc_idx = self._video_buffer.append_coordinate(i-1, c)
                        # and obviously add the id in the buffer
                        self._video_buffer.set_id(i-1, nc_idx, kid)

            else:
                # the kid is not detected at i, and it wasn't at
                # i-2 but it was at i-1.
                if here[0] is False and here[1] is True:
                    self.__dissociate_kid_coord(i-1, kid)
                    here[1] = False

            # shift for next image
            here[0] = here[1]
            here[1] = here[2]
            here[2] = False

    # -----------------------------------------------------------------------

    def _reduce_population(self, nb_kids):
        """Remove data of the most rarely detected kids in the buffer.

        :param nb_kids: (int) Max number of kids to be detected

        """
        # check if there is something to do
        how_many = len(self.__kidsim) - nb_kids
        if how_many <= 0:
            return 0

        # Estimate the number of times each kid is detected in this buffer
        count_coords = collections.Counter(self._count_buffer_kids())

        # Get the kids we observed the most frequently
        frequents = collections.Counter(dict(count_coords.most_common(nb_kids)))
        # and deduce the identifiers we observed the most rarely
        rare_ids = tuple(x for x in count_coords - frequents)

        # Dissociate the un-relevant kids
        for i in range(len(self._video_buffer)):
            for kid in rare_ids:
                self.__dissociate_kid_coord(i, kid)

    # -----------------------------------------------------------------------

    def _dissociate_rare_and_scattered(self, percent=15., n=4):
        """Remove coords of kids appearing/disappearing like blinking.

        Consider to remove the kid only if the detected coords are
        occurring less than given percent of the buffer images

        :param percent: (float) Percentage threshold.
        :param n: n-gram used to know if data are scattered or not

        """
        # Estimate the number of times each kid is detected
        count_coords = self._count_buffer_kids()

        # A kid is rare if it's coords are detected in less than '%' images
        rare_ids = list()
        for kid in count_coords:
            freq_pid = 100. * float(count_coords[kid]) / float(len(self._video_buffer))
            if freq_pid < percent:
                rare_ids.append(kid)

        # Remove these rare kids ONLY if their coords are not continuous
        for kid in rare_ids:
            # Are they continuous or scattered?
            scattered = False
            # Estimate the N-grams of detected/non detected states
            states = [False]*len(self._video_buffer)
            for i in range(len(self._video_buffer)):
                if kid in self._video_buffer.get_ids(i):
                    states[i] = True
            true_ngram = tuple([True]*n)
            ngrams = symbols_to_items(states, n)
            # Estimate the ratio of sequences of 'n' true states
            if true_ngram in ngrams:
                ngrams_of_kid = ngrams[true_ngram]
                # the nb of possible sequences of kid->...->kid is nb_images-n-1
                ratio = float(ngrams_of_kid) / float(len(self._video_buffer) - n - 1)
                if ratio < 0.25:
                    scattered = True
            else:
                scattered = True

            # the kid is rare and its coords are scattered
            if scattered is True:
                for i in range(len(self._video_buffer)):
                    self.__dissociate_kid_coord(i, kid)

    # -----------------------------------------------------------------------

    def _count_buffer_kids(self):
        """Estimate the number of images in which each kid is detected.

        :return: (dict) key=kid, value=number of images

        """
        count_coords = dict()
        for kid in self.__kidsim:
            count_coords[kid] = 0

        for i in range(len(self._video_buffer)):
            for kid in self._video_buffer.get_ids(i):
                # if this kid was not already dissociated
                if kid in self.__kidsim:
                    count_coords[kid] += 1

        return count_coords

    # -----------------------------------------------------------------------

    def _set_identity_by_similarity(self):
        """Set a kid to each coord of the buffer with image similarities.

        """
        for i in range(len(self._video_buffer)):
            image = self._video_buffer[i]
            coords_i = self._video_buffer.get_coordinates(i)

            # for each of the coordinates, assign a kid
            identified = list()
            for f, c in enumerate(coords_i):
                # Use similarity to identify which kid is matching the coords
                # or if none of them. Priority is given to coords similarity.
                identity, score = self.__kidsim.identify(image=None, coords=c)
                if identity is None:
                    # Coords are not matching enough. Rescue with the image similarities.
                    img = image.icrop(c)
                    identity, score = self.__kidsim.identify(image=img, coords=None)
                # The similarity measure identified a kid
                if identity is not None:
                    # Verify if this kid was not already assigned to a previous coord of this image.
                    for j in range(len(identified)):
                        identitj, scorj = identified[j]
                        # a kid is identified at 2 different coords: f and j
                        if identity == identitj:
                            # keep only the best score, invalidate the other one
                            if scorj < score:
                                identified[j] = (None, 0.)
                            else:
                                identity = None
                                score = 0.
                                break

                # Store the information for next coords
                identified.append((identity, score))

            # So, now that we know who is where... we can store the information
            for f, c in enumerate(coords_i):
                identity, score = identified[f]
                if identity is None:
                    # Either the similarity does NOT identified a kid, or,
                    # a kid was identified then invalidated
                    self._video_buffer.set_id(i, f, "unknown")
                else:
                    # Yep! the coords are matching a kid
                    self._video_buffer.set_id(i, f, identity)
                    self.__kidsim.set_cur_coords(identity, c)

    # -----------------------------------------------------------------------

    def __create_kid(self, image_index, coords_index):
        """Create and add a new kid.
        
        """
        coords_i = self._video_buffer.get_coordinates(image_index)

        image = self._video_buffer[image_index]
        img_kid = image.icrop(coords_i[coords_index])
        kid = self.__kidsim.create_identifier()
        self.__kidsim.add_image(kid, img_kid, reference=True)
        self.__kidsim.set_ref_coords(kid, coords_i[coords_index])

        # set the kid to the buffer
        self._video_buffer.set_id(image_index, coords_index, kid)

        return kid

    # -----------------------------------------------------------------------

    def __dissociate_kid_coord(self, buffer_index, kid):
        """Dissociate the kid to its assigned coord at given image.

        """
        if buffer_index < 0:
            return

        all_ids = self._video_buffer.get_ids(buffer_index)
        if kid in all_ids:
            idx = all_ids.index(kid)
            # fix and set the default identifier at this index
            identifier = "unk_{:03d}".format(idx+1)
            self._video_buffer.set_id(buffer_index, idx, identifier)
