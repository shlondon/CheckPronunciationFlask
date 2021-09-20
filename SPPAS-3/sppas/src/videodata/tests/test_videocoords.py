"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech

        http://www.sppas.org/

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

    src.videodata.tests.test_videocoords.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import unittest
import os
import numpy as np

from sppas.src.config import paths
from sppas.src.imgdata import sppasCoords
from ..videocoords import sppasCoordsVideoBuffer
from ..videocoords import sppasCoordsVideoWriter
from ..videobuffer import sppasVideoReaderBuffer

# ---------------------------------------------------------------------------


class TestVideoCoords(unittest.TestCase):

    VIDEO = os.path.join(paths.samples, "faces", "video_sample.mp4")

    # -----------------------------------------------------------------------

    def test_init(self):
        bv = sppasCoordsVideoBuffer()
        self.assertFalse(bv.is_opened())

        self.assertEqual(bv.get_buffer_size(), sppasVideoReaderBuffer.DEFAULT_BUFFER_SIZE)
        self.assertEqual(bv.get_buffer_overlap(), sppasVideoReaderBuffer.DEFAULT_BUFFER_OVERLAP)
        self.assertFalse(bv.is_opened())
        self.assertEqual(0., bv.get_framerate())
        self.assertEqual(0, bv.tell())

    # -----------------------------------------------------------------------

    def test_coords(self):
        bv = sppasCoordsVideoBuffer(TestVideoCoords.VIDEO, size=50)

        # Add coords but buffer is empty
        with self.assertRaises(ValueError):
            bv.append_coordinate(10, sppasCoords(10, 10))

        # Fill in the first buffer of images
        res = bv.next()
        self.assertEqual(50, bv.tell())
        self.assertEqual(50, len(bv))
        self.assertEqual((0, 49), bv.get_buffer_range())
        self.assertTrue(res)  # we did not reached the end of the video

        # Add/Get coord
        c = sppasCoords(10, 10, 100, 100)
        bv.append_coordinate(10, c)
        c_ret = bv.get_coordinate(10, 0)
        self.assertTrue(c is c_ret)

        # Pop coord
        bv.pop_coordinate(10, 0)
        coords = bv.get_coordinates(10)
        self.assertEqual(0, len(coords))

        # Remove coord
        bv.append_coordinate(10, c)
        coords = bv.get_coordinates(10)
        self.assertEqual(1, len(coords))
        bv.remove_coordinate(10, c)
        coords = bv.get_coordinates(10)
        self.assertEqual(0, len(coords))
