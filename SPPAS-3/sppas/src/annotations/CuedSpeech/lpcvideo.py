# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.CuedSpeech.lpcvideo.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Tag a video with the Cued Speech keys.

.. _This file is part of SPPAS: <http://www.sppas.org/>
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
from sppas.src.anndata import sppasTier
from sppas.src.videodata import sppasVideoWriter
from sppas.src.imgdata import sppasCoords

from sppas.src.annotations.FaceSights import sppasSightsVideoReader
from sppas.src.annotations.FaceSights import Sights

from .videokeys import sppasKeysVideoBuffer
from .videokeys import sppasKeysVideoWriter

# ---------------------------------------------------------------------------

MSG_ERROR_MISMATCH = "The given {:d} coordinates in CSV file doesn't match " \
                     "the number of frames of the video {:d}"

# ---------------------------------------------------------------------------


class CuedSpeechVideoTagger(object):
    """Create a video with hands tagged on the face of a video.

    """

    def __init__(self, video=None, csv_sights=None):
        """Create a new instance.

        :param video: (str) Filename of the input video
        :param csv_sights: (str) Filename of the CSV with sights

        """
        self.__data = None
        self.__video_buffer = sppasKeysVideoBuffer()
        self.__video_writer = sppasKeysVideoWriter()
        self.__video_writer.set_options(csv=False, folder=False, tag=True, crop=False)

        if video is not None and csv_sights is not None:
            self.load(video, csv_sights)

    # -----------------------------------------------------------------------

    def load(self, video, csv_sights):
        """Open the video and load the CVS data.

        :param video: (str) Filename of the input video
        :param csv_sights: (str) Filename of the CSV with sights

        """
        self.close()

        # Open the CSV file dans load all its data
        self.__data = sppasSightsVideoReader(csv_sights)
        # Only one kid is expected
        for entry in self.__data.ids:
            if len(entry) > 1:
                raise ValueError("Only one identified face was expected. Get {:d}."
                                 "".format(len(entry)))

        # Open the video file
        self.__video_buffer.open(video)

        # The nb of lines in the CSV must correspond to the number of frames of the video
        nframes = self.__video_buffer.get_nframes()
        if len(self.__data.coords) != nframes:
            # Release the video stream
            self.__video_buffer.close()
            self.__video_buffer.reset()
            raise sppasError(MSG_ERROR_MISMATCH.format(len(self.__data.coords), nframes))

        # Adjust the video writer
        self.__video_writer.set_fps(self.__video_buffer.get_framerate())

    # -----------------------------------------------------------------------

    def close(self):
        """Release video streams."""
        if self.__video_buffer is not None:
            self.__video_buffer.close()
        if self.__video_writer is not None:
            self.__video_writer.close()

    # -----------------------------------------------------------------------

    def __del__(self):
        self.close()

    # -----------------------------------------------------------------------

    def tag(self, syll_keys, output):
        """Tag the video with the given keys.

        :param syll_keys: (sppasTier)
        :param output: Output video filename
        :return: list of created files -- expected 1

        """
        if self.__video_buffer is None:
            return ()
        if self.__video_buffer.is_opened() is False:
            return ()

        result = list()
        i = 0   # index of the first image of each buffer
        nb = 0  # buffer number
        read_next = True    # reached the end of the video or not
        self.__video_buffer.seek_buffer(0)

        while read_next is True:
            logging.info(" ... buffer number {:d}".format(nb + 1))

            # Fill-in the buffer with images
            read_next = self.__video_buffer.next()

            # Use the 68 face sights to fix the positions of the 5 possible keys
            self.__fix_vowels_position(self.__data.sights[i:i+len(self.__video_buffer)])

            # Browse the tier to fix the key of each image of the buffer
            image_duration = 1. / self.__video_buffer.get_framerate()
            start_time = float(i) * image_duration
            end_time = float(i + len(self.__video_buffer)) * image_duration
            self.__fix_keys(start_time, end_time, syll_keys)

            # Save the current result in a video
            if output is not None:
                new_files = self.__video_writer.write(self.__video_buffer, output, "")
                result.extend(new_files)

            nb += 1
            i += len(self.__video_buffer)

        return result

    # -----------------------------------------------------------------------

    def __fix_vowels_position(self, all_sights):
        """Fix the 5 vowels positions in each image of the buffer.

        :param all_sights: (list of 68 sights)

        """
        kid_sights = Sights(nb=68)
        for buf_idx, sights in enumerate(all_sights):
            # Get the sights of the kid in the image or use the previous ones
            if len(sights) > 0:
                kid_sights = sights[0]

            # Among the 68, get the sights needed to fix the 5 positions of the keys
            x0, y0, s0 = kid_sights.get_sight(0)
            x2, y2, s2 = kid_sights.get_sight(2)
            x8, y8, s8 = kid_sights.get_sight(8)
            x36, y36, s36 = kid_sights.get_sight(36)
            x48, y48, s48 = kid_sights.get_sight(48)
            x57, y57, s57 = kid_sights.get_sight(57)
            x60, y60, s60 = kid_sights.get_sight(60)

            # Position 1 is close to the left eye
            x = x0 + ((x36 - x0) // 2)
            y = y0 + (y0 - y36)
            c1 = sppasCoords(x, y, confidence=s0)

            # Position 2 is in the middle of the chin
            x = x8
            y = y8 - ((y8 - y57) // 4)
            c2 = sppasCoords(x, y, confidence=s8)

            # Position 3 is on the left side of the face
            x = max(0, x2 - (x36 - x0))
            y = y2
            c3 = sppasCoords(x, y, confidence=s2)

            # Position 4 is at the left of the lips
            x = x48 - (x60 - x48)
            y = y48 + ((y57 - y48) // 2)
            c4 = sppasCoords(x, y, confidence=s48)

            # Position 5 is at the glottis
            x = x8
            y = y8 + (y8-y57)
            c5 = sppasCoords(x, y, confidence=s57)

            self.__video_buffer.set_coordinates(buf_idx, [c1, c2, c3, c4, c5])

    # -----------------------------------------------------------------------

    def __fix_keys(self, start_time, end_time, syll_tier):
        """Fix the key of each image of the buffer.

        :return: (list of tuples) List of vowel-consonant

        """
        # Create a tier with only the annotations of the buffer to increase
        # all the "find" needed later to browse the annotations
        anns = syll_tier.find(start_time, end_time, overlaps=True)
        tier = sppasTier("")
        for a in anns:
            tier.add(a)

        image_duration = 1. / self.__video_buffer.get_framerate()
        for buf_idx, image in enumerate(self.__video_buffer):
            # Get the annotations during the image
            s = start_time + (buf_idx * image_duration)
            e = s + image_duration
            anns = tier.find(s, e, overlaps=True)
            if len(anns) == 0:
                # There no key assigned to the image
                self.__video_buffer.set_key(buf_idx, "0", "0")
            elif len(anns) == 1:
                # A key is matching the image time
                labels = anns[0].get_labels()
                if len(labels) == 2:
                    consonant = labels[0].get_best().get_content()
                    vowel = labels[1].get_best().get_content()
                    self.__video_buffer.set_key(buf_idx, consonant, vowel)
                else:
                    raise ValueError(
                        "Two labels (consonant, vowel) were expected in "
                        "CuedSpeech. Got {:d} instead.".format(len(labels)))
            else:
                # There are several keys assigned to the image.
                # It is probably a transition between 2 keys but both are
                # too short in time to be drawn.
                self.__video_buffer.set_key(buf_idx, "0", "0")
