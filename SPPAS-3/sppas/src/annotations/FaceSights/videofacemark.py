# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.videofacemark.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic detection of the 68 sights on faces of a video.

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

from sppas.src.exceptions import sppasError
from sppas.src.videodata import sppasCoordsVideoReader

from .videosights import sppasSightsVideoBuffer
from .imgfacemark import ImageFaceLandmark

# ---------------------------------------------------------------------------


class VideoFaceLandmark(object):
    """Estimate the 68 face sights on all faces of a video.

    If faces were previously detected, this result can be loaded from a CSV
    file but if not, a FD system must be declared when initializing this class.

    """

    def __init__(self, face_landmark, face_detection=None):
        """Create a new instance.

        :param face_landmark: (ImageFaceLandmark) FL image system
        :param face_detection: (ImageFaceDetection) FD image system

        """
        # The face detection system
        if isinstance(face_landmark, ImageFaceLandmark) is False:
            raise sppasError("A face detection system was expected.")

        self._video_buffer = sppasSightsVideoBuffer()
        self.__fl = face_landmark
        self.__fd = face_detection

    # -----------------------------------------------------------------------
    # Automatic detection of the face sights in a video
    # -----------------------------------------------------------------------

    def video_face_sights(self, video, csv_faces=None, video_writer=None, output=None):
        """Browse the video, get faces then detect sights and write results.

        :param video: (str) Video filename
        :param csv_faces: (str) Filename with the coords of all faces
        :param video_writer: ()
        :param output: (str) The output name for the folder and/or the video

        :return: (list) The coordinates of all detected sights on all images

        """
        # The detection system isn't ready
        if self.__fl.get_nb_recognizers() == 0:
            raise sppasError("A landmark recognizer must be initialized first")

        # Browse the video using the buffer of images
        result = list()
        read_next = True
        nb = 0
        i = 0

        # Open the video stream
        self._video_buffer.open(video)
        self._video_buffer.seek_buffer(0)
        if video_writer is not None:
            video_writer.set_fps(self._video_buffer.get_framerate())

        # Get coordinates of the faces -- if previously estimated
        coords_buffer = None
        if csv_faces is not None:
            br = sppasCoordsVideoReader(csv_faces)
            coords_buffer = br.coords
            nframes = self._video_buffer.get_nframes()
            if len(coords_buffer) != nframes:
                logging.error("The given {:d} coordinates doesn't match the"
                              " number of frames of the video {:d}"
                              "".format(len(coords_buffer), nframes))
                coords_buffer = None

        if coords_buffer is None and self.__fd is None:
            # Release the video stream
            self._video_buffer.close()
            self._video_buffer.reset()
            raise sppasError("Face sights estimation requires faces or a "
                             "face detection system. None of them was declared.")

        while read_next is True:
            logging.info("Read buffer number {:d}".format(nb+1))

            # fill-in the buffer with 'size'-images of the video
            read_next = self._video_buffer.next()

            # face sights on the current images of the buffer
            if coords_buffer is not None:
                # get face coordinates from the CSV
                self._detect_buffer(coords_buffer[i:i+len(self._video_buffer)])
            else:
                # estimate face coordinates from the FD system
                self._detect_buffer()

            # save the current results: file names or list of face coordinates
            if output is not None and video_writer is not None:
                new_files = video_writer.write(self._video_buffer, output)
                result.extend(new_files)
            else:
                for i in range(len(self._video_buffer)):
                    faces = self._video_buffer.get_coordinates(i)
                    result.append(faces)

            nb += 1
            i += len(self._video_buffer)

        # Release the video stream
        self._video_buffer.close()
        self._video_buffer.reset()

        return result

    # -----------------------------------------------------------------------

    def _detect_buffer(self, coords=None):
        """Determine the sights of all the detected faces of all images.

        :raise: sppasError if no model was loaded or no faces.

        """
        # No buffer is in-use.
        if len(self._video_buffer) == 0:
            logging.warning("Nothing to detect: no images in the buffer.")
            return

        # Find the sights of faces in each image.
        for i, image in enumerate(self._video_buffer):
            if coords is None:
                self.__fd.detect(image)
                faces = [c.copy() for c in self.__fd]
            else:
                faces = coords[i]
            self._video_buffer.set_coordinates(i, faces)

            # Perform detection on all faces in the current image
            if len(faces) > 0:
                for f, face_coord in enumerate(faces):
                    self.__fl.detect_sights(image, face_coord)
                    # Save results into the list of sights of such image
                    self._video_buffer.set_sight(i, f, self.__fl.get_sights())

            if self.__fd is not None:
                self.__fd.invalidate()
            self.__fl.invalidate()
