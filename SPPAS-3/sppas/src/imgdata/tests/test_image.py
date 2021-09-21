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

    src.imgdata.tests.test_image.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import unittest
import cv2
import numpy

from sppas.src.config import paths
from ..coordinates import sppasCoords
from ..image import sppasImage

# ---------------------------------------------------------------------------


class TestImage(unittest.TestCase):

    # a JPG image has no transparency, so shape is 3
    fn = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016.jpg")

    def test_init(self):
        img = cv2.imread(TestImage.fn)
        self.assertEqual(len(img), 803)

        i1 = sppasImage(input_array=img)
        self.assertIsInstance(i1, numpy.ndarray)
        self.assertIsInstance(i1, sppasImage)
        self.assertEqual(len(img), len(i1))
        self.assertTrue(i1 == img)

        i2 = sppasImage(filename=TestImage.fn)
        self.assertIsInstance(i2, numpy.ndarray)
        self.assertIsInstance(i2, sppasImage)
        self.assertEqual(len(img), len(i2))
        self.assertTrue(i2 == img)

        with self.assertRaises(IOError):
            sppasImage(filename="toto.jpg")

        self.assertEqual(3, i2.shape[2])
        self.assertEqual(3, i2.channel)

    # -----------------------------------------------------------------------

    def test_size(self):
        img = sppasImage(filename=TestImage.fn)
        self.assertEqual(1488, img.width)
        self.assertEqual(803, img.height)
        self.assertEqual(3, img.channel)
        self.assertEqual((1488, 803), img.size())
        self.assertEqual((744, 401), img.center)

    # -----------------------------------------------------------------------

    def test_memory_usage(self):
        img = cv2.imread(TestImage.fn)
        i1 = sppasImage(input_array=img)
        self.assertEqual(1488, i1.width)
        self.assertEqual(803, i1.height)
        self.assertEqual(3, i1.channel)

        # Each (r,g,b) is 3 bytes (uint8)
        self.assertEqual(803*1488*3, i1.nbytes)

    # -----------------------------------------------------------------------

    def test_dist(self):
        img = cv2.imread(TestImage.fn)
        i1 = sppasImage(input_array=img)
        w, h = i1.size()
        d = i1.euclidian_distance(i1)
        self.assertEqual(d, 0.)

        # distance compared to black
        blank = sppasImage(0).blank_image(w, h)
        d = i1.euclidian_distance(blank)
        self.assertEqual(3.67896, round(d, 5))

        # distance compared to red
        red = i1.ired()
        d = i1.euclidian_distance(red)
        self.assertEqual(2.48066, round(d, 5))

        # distance compared to green
        green = i1.igreen()
        d = i1.euclidian_distance(green)
        self.assertEqual(2.46968, round(d, 5))

        # distance compared to blue
        blue = i1.iblue()
        d = i1.euclidian_distance(blue)
        self.assertEqual(2.40758, round(d, 5))

    # -----------------------------------------------------------------------

    def test_blank(self):
        blank = sppasImage(0).blank_image(100, 200)
        self.assertEqual(100, blank.width)
        self.assertEqual(200, blank.height)
        self.assertEqual(3, blank.channel)

        img = sppasImage(filename=TestImage.fn)
        blank = img.blank_image()
        self.assertEqual(1488, blank.width)
        self.assertEqual(803, blank.height)
        self.assertEqual(3, blank.channel)

        blank = img.blank_image(w=1000)
        self.assertEqual(1000, blank.width)
        self.assertEqual(803, blank.height)
        self.assertEqual(3, blank.channel)

        blank = img.blank_image(h=1000)
        self.assertEqual(1488, blank.width)
        self.assertEqual(1000, blank.height)
        self.assertEqual(3, blank.channel)

    # -----------------------------------------------------------------------

    def test_crop(self):
        image = sppasImage(filename=TestImage.fn)
        cropped = image.icrop(sppasCoords(886, 222, 177, 189))
        # The cropped image is 189 rows and 177 columns of pixels
        self.assertEqual(189, len(cropped))
        for row in cropped:
            self.assertEqual(len(row), 177)

        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-face.jpg")
        cropped.write(fnc)
        self.assertTrue(os.path.exists(fnc))
        cropped_read = sppasImage(filename=fnc)
        os.remove(fnc)

        self.assertEqual(189, len(cropped_read))
        for row in cropped_read:
            self.assertEqual(len(row), 177)

        # test if same shape, same elements values
        # self.assertTrue(numpy.array_equal(cropped, cropped_read))

        # test if broadcastable shape, same elements values
        # self.assertTrue(numpy.array_equiv(cropped, cropped_read))

    # -----------------------------------------------------------------------

    def test_gray(self):
        image = sppasImage(filename=TestImage.fn)

        result = image.igray()
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020-gray.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_bgr(self):
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-0.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        image = sppasImage(filename=sample)

        result = image.ibgr((0, 156, 32))
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020-green.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_alpha(self):
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-0.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        image = sppasImage(filename=sample)

        result = image.ialpha(64, direction=1)
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020-alpha.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_paste(self):
        image = sppasImage(filename=TestImage.fn)
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-0.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        other = sppasImage(filename=sample)

        pasted = image.ipaste(other, [100, 200, 300, 70])
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-paste.png")
        pasted.write(fnc)

    # -----------------------------------------------------------------------

    def test_overlay(self):
        image = sppasImage(filename=TestImage.fn)
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        other = sppasImage(filename=sample)

        result = image.ioverlay(other, coord=(700, 300, 300, 200))
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-overlay.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_flip(self):
        image = sppasImage(filename=TestImage.fn)

        result = image.iflip()
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-flipped.jpg")
        # result.write(fnc)

    # -----------------------------------------------------------------------

    def test_blend(self):
        image = sppasImage(filename=TestImage.fn)
        other = sppasImage(filename=os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png"))

        result = image.iblend(other, coord=(100, 100, 200, 200), weight1=0.8, weight2=0.5)
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-blended.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_contour(self):
        image = sppasImage(filename=TestImage.fn)

        result = image.icontours()
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-contour.jpg")
        # result.write(fnc)

    # -----------------------------------------------------------------------

    def test_blur(self):
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        image = sppasImage(filename=sample)

        result = image.iblur()
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-blur.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_mask(self):
        image = sppasImage(filename=TestImage.fn)

        # we use the contours as mask
        contours = image.icontours(threshold=100, color=(255, 255, 255))
        blur = contours.iblur()
        cropped = blur.icrop(sppasCoords(86, 222, 177, 189))

        result = image.imask(cropped)
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-mask.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_overlays(self):
        image = sppasImage(filename=TestImage.fn)
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        other = sppasImage(filename=sample)

        from_coords = (100, 0, 200, 200)
        to_coords = (800, 800, 600, 600)

        results = image.ioverlays(other, from_coords, to_coords, 10)
        fnc = os.path.join(paths.samples, "faces", "BrigitteBigiSlovenie2016-over")
        for i in range(len(results)):
            fnci = fnc + str(i+1) + ".jpg"
            results[i].write(fnci)

    # -----------------------------------------------------------------------

    def test_shift(self):
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        image = sppasImage(filename=sample)
        result = image.ishift(60, -120)
        fnc = os.path.join(paths.samples, "faces", "shift.png")
        result.write(fnc)

    # -----------------------------------------------------------------------

    def test_shadow(self):
        sample = os.path.join(paths.resources, "lpc", "hand-lfpc-1.png")
        if os.path.exists(sample) is False:
            sample = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        image = sppasImage(filename=sample)
        result = image.ishadow(5, 20)
        fnc = os.path.join(paths.samples, "faces", "shadow.png")
        result.write(fnc)
