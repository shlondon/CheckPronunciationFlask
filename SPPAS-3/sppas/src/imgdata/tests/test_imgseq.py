"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech

        http://www.sppas.org/

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

    src.imgdata.tests.test_imgseq.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import unittest
import cv2
import numpy

from sppas.src.config import paths
from ..coordinates import sppasCoords
from ..image import sppasImage
from ..imgsequence import ImageSequence

# ---------------------------------------------------------------------------


class TestImageSequence(unittest.TestCase):

    # a JPG image has no transparency, so shape is 3
    fn = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016.jpg")

    # -----------------------------------------------------------------------

    def test_overlays(self):
        image = sppasImage(filename=TestImageSequence.fn)
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        other = sppasImage(filename=sample)

        from_coords = (100, 0, 200, 200)
        to_coords = (800, 800, 600, 600)

        iseq = ImageSequence(image)
        results = iseq.overlays(other, from_coords, to_coords, 10)
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-over")
        for i in range(len(results)):
            fnci = fnc + str(i+1) + ".jpg"
            results[i].write(fnci)
