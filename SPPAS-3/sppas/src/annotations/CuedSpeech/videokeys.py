# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.CuedSpeech.videokeys.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Video buffer and writer for the Cued Speech keys.

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
from sppas.src.imgdata import sppasCoordsImageWriter
from sppas.src.videodata import sppasVideoWriter
from sppas.src.videodata import sppasCoordsVideoBuffer
from sppas.src.videodata import sppasCoordsVideoWriter

# ---------------------------------------------------------------------------


class sppasKeysVideoBuffer(sppasCoordsVideoBuffer):
    """A video buffer with lists of coordinates and keys.

    For each image of the buffer, the coordinates is a list of the 5 positions
    of the vowels on a face and the key is a tuple with the Cued Speech key
    made of a consonant and a vowel identifier.

    """

    def __init__(self, video=None, size=-1):
        """Create a new instance.

        :param video: (str) The video filename
        :param size: (int) Number of images of the buffer or -1 for auto

        """
        super(sppasKeysVideoBuffer, self).__init__(video, size=size)

        self.__conson = list()
        self.__vowel = list()
        self.__init_keys()

    # -----------------------------------------------------------------------

    def __init_keys(self):
        # The list of list of sights
        self.__conson = [None] * self.get_buffer_size()
        self.__vowel = [None] * self.get_buffer_size()

    # -----------------------------------------------------------------------

    def reset(self):
        """Override. Reset all the info related to the buffer content."""
        sppasCoordsVideoBuffer.reset(self)
        self.__init_keys()

    # -----------------------------------------------------------------------

    def next(self):
        """Override. Fill in the buffer with the next images & reset keys.

        """
        ret = sppasCoordsVideoBuffer.next(self)
        self.__init_keys()
        return ret

    # -----------------------------------------------------------------------

    def get_key(self, buffer_index):
        """Return the (consonant, vowel) key of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :return: tuple()

        """
        buffer_index = self.check_buffer_index(buffer_index)
        return self.__conson[buffer_index], self.__vowel[buffer_index]

    # -----------------------------------------------------------------------

    def set_key(self, buffer_index, consonant, vowel):
        """Set the key to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param consonant: (str) the given consonant
        :param vowel: (str) the given vowel

        """
        buffer_index = self.check_buffer_index(buffer_index)
        self.__conson[buffer_index] = consonant
        self.__vowel[buffer_index] = vowel

# ---------------------------------------------------------------------------


class sppasKeysImageWriter(sppasCoordsImageWriter):
    """Tag&Write an image.

    """

    def __init__(self):
        """Create a new sppasSightsImageWriter instance.

        Write the given image in the given filename.
        Five colors are fixed to draw the vowels positions:
            - Key of vowels 1 is pink (200, 0, 100)
            - Key of vowels 2 is orange (255, 128, 0)
            - Key of vowels 3 is blue (0, 128, 255)
            - Key of vowels 4 is red (205, 0, 0)
            - Key of vowels 5 is green (0, 175, 0)

        """
        super(sppasKeysImageWriter, self).__init__()

        # Reset the colors to fix custom ones
        self._colors = dict()
        self._colors['b'] = [200, 255, 0, 205, 0]
        self._colors['g'] = [0, 128, 128, 0, 175]
        self._colors['r'] = [100, 0, 255, 0, 0]

# ---------------------------------------------------------------------------


class sppasKeysVideoWriter(sppasCoordsVideoWriter):
    """Write a video with keys.

    """

    def __init__(self, image_writer=None):
        """Create a new instance.

        """
        super(sppasKeysVideoWriter, self).__init__()

        # Override.
        self._img_writer = sppasKeysImageWriter()

    # -----------------------------------------------------------------------

    def write_video(self, video_buffer, out_name, pattern):
        """Save the result in video format.

        :param video_buffer: (sppasImage) The image to write
        :param out_name: (str) The filename of the output video file
        :param pattern: (str) Pattern to add to cropped video filename(s)
        :return: list of newly created video file names

        """
        new_files = list()

        iter_images = video_buffer.__iter__()
        for i in range(video_buffer.__len__()):
            image = next(iter_images)

            # Get the list of coordinates stored for the i-th image
            coords = video_buffer.get_coordinates(i)

            # Create the sppasVideoWriter() if it wasn't already done.
            # An image is required to properly fix the video size.
            if self._tag_video_writer is None:
                self._tag_video_writer, fn = self.create_video_writer(out_name, image, pattern)
                new_files.append(fn)

            # Tag the image with circles at the coords of keys
            img = self._img_writer.tag_image(image, coords)

            # Tag the image with the key
            consonant, vowel = video_buffer.get_key(i)

            if vowel in ("1", "2", "3", "4", "5"):
                # the coordinates of the key
                v = int(vowel) - 1
                coord = video_buffer.get_coordinate(i, v)
                colors = self._img_writer.get_colors()
                color = (colors['r'][v], colors['g'][v], colors['b'][v])
                # print("Put key c={} v={} at image {:d} at {}-{} with color {}".format(consonant, vowel, i, coord.x, coord.y, color))
                img.put_text(coord, color, thickness=2, text=consonant)

            # Write the tagged image into the video
            self._tag_video_writer.write(img)

        return new_files
