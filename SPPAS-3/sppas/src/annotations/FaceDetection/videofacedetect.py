# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceDetection.videofacedetect.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic detection of faces in a video.

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

"""

import logging

from sppas.src.config import sppasError
from sppas.src.videodata import sppasCoordsVideoBuffer

from .imgfacedetect import ImageFaceDetection

# ---------------------------------------------------------------------------


class VideoFaceDetection(object):
    """Search for faces on all images of a video.

    """

    def __init__(self, face_detection):
        """Create a new instance.

        :param face_detection: (ImageFaceDetection) FD image system

        """
        # The face detection system
        if isinstance(face_detection, ImageFaceDetection) is False:
            raise sppasError("A face detection system was expected.")

        self._video_buffer = sppasCoordsVideoBuffer()

        # Configure the face detection system
        self.__fd = face_detection
        self.__confidence = face_detection.get_min_score()
        self.__nbest = 0
        self.__portrait = True

    # -----------------------------------------------------------------------

    def get_filter_confidence(self):
        """Return the min scores of faces to detect."""
        return self.__confidence

    # -----------------------------------------------------------------------

    def set_filter_confidence(self, value=0.2):
        """Force to detect only the faces with a confidence score > value.

        It means that any detected face with a score lesser than the given
        one will be ignored. The score of detected faces are supposed to
        range between 0. and 1.

        :param value: (float) Value ranging [0., 1.]
        :raise: ValueError

        """
        self.__confidence = value

    # -----------------------------------------------------------------------

    def get_filter_best(self):
        """Return the max nb of faces to detect."""
        return self.__nbest

    # -----------------------------------------------------------------------

    def set_filter_best(self, value=-1):
        """Force to detect at max the given number of faces.

        :param value: (int) Number of faces to detect or -1 to not force.

        """
        value = int(value)
        self.__nbest = value

    # -----------------------------------------------------------------------

    def set_portrait(self, value=True):
        """Consider the portrait instead of the face.

        :param value: (bool)

        """
        self.__portrait = bool(value)

    # -----------------------------------------------------------------------
    # Automatic detection of the faces in a video
    # -----------------------------------------------------------------------

    def video_face_detect(self, video, video_writer=None, output=None):
        """Browse the video, detect faces and write results.

        :param video: (str) Video filename
        :param video_writer: ()
        :param output: (str) The output name for the folder and/or the video

        :return: (list) The coordinates of all detected faces on all images

        """
        # Browse the video using the buffer of images
        result = list()
        read_next = True
        nb = 0

        # Open the video stream
        self._video_buffer.open(video)
        self._video_buffer.seek_buffer(0)
        video_writer.set_fps(self._video_buffer.get_framerate())

        while read_next is True:
            logging.info("Buffer number {:d}".format(nb+1))

            # fill-in the buffer with 'size'-images of the video
            read_next = self._video_buffer.next()

            # face detection on the current images of the buffer
            self.detect_buffer()

            # save the current results: file names or list of face coordinates
            if output is not None and video_writer is not None:
                new_files = video_writer.write(self._video_buffer, output)
                result.extend(new_files)
            else:
                for i in range(len(self._video_buffer)):
                    faces = self._video_buffer.get_coordinates(i)
                    result.append(faces)

            nb += 1

        # Release the video stream
        self._video_buffer.close()
        self._video_buffer.reset()

        return result

    # -----------------------------------------------------------------------
    # Work on a buffer...
    # -----------------------------------------------------------------------

    def detect_buffer(self):
        """Search for faces in the currently loaded buffer of the video.

        Determine the coordinates of all the detected faces of all images.
        They are ranked from the highest score to the lowest one.

        :raise: sppasError if no model was loaded.

        """
        # No buffer is in-use.
        if len(self._video_buffer) == 0:
            logging.warning("Nothing to detect: no images in the buffer.")
            return

        # The detection system isn't ready
        if self.__fd.get_nb_recognizers() == 0:
            raise sppasError("A face detector must be initialized first.")

        # Find the coordinates of faces in each image.
        for i, image in enumerate(self._video_buffer):

            # Perform face detection to detect all faces in the current image
            self.__fd.detect(image)

            # Apply filters to keep the better ones
            if self.__nbest != 0:
                self.__fd.filter_best(self.__nbest)
            self.__fd.filter_confidence(self.__confidence)

            # Resize the detected face to the portrait
            if self.__portrait is True:
                self.__fd.to_portrait(image)

            # Save results into the list of coordinates of such image
            coords = [c.copy() for c in self.__fd]
            self._video_buffer.set_coordinates(i, coords)
            self.__fd.invalidate()
