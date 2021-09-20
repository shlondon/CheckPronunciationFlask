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

    src.annotations.tests.test_facesights.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import unittest

from sppas.src.config import paths
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import sppasCoordsImageWriter
from sppas.src.imgdata import sppasCoords

from ..FaceDetection import ImageFaceDetection
from ..FaceSights.sights import Sights
from ..FaceSights.imgfacemark import ImageFaceLandmark
from ..FaceSights.videofacemark import VideoFaceLandmark

# ---------------------------------------------------------------------------

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MODEL_LBF68 = os.path.join(paths.resources, "faces", "lbfmodel68.yaml")
MODEL_DAT = os.path.join(paths.resources, "faces", "kazemi_landmark.dat")
# --> not efficient: os.path.join(paths.resources, "faces", "aam.xml")

NET = os.path.join(paths.resources, "faces", "res10_300x300_ssd_iter_140000_fp16.caffemodel")
HAAR1 = os.path.join(paths.resources, "faces", "haarcascade_profileface.xml")
HAAR2 = os.path.join(paths.resources, "faces", "haarcascade_frontalface_alt.xml")

# ---------------------------------------------------------------------------


class TestSights(unittest.TestCase):

    def test_init(self):
        s = Sights()
        self.assertEqual(68, len(s))

        s = Sights(5)
        self.assertEqual(5, len(s))
        for i in range(5):
            self.assertEqual((-1, -1, None), s.get_sight(0))

        with self.assertRaises(TypeError):
            Sights(-1)
        with self.assertRaises(TypeError):
            Sights(1.6)

    # ------------------------------------------------------------------------

    def test_get_set(self):
        s = Sights(5)
        s.set_sight(0, 10, 20)
        self.assertEqual((10, 20, None), s.get_sight(0))
        s.set_score(0, 0.123)
        self.assertEqual(0.123, s.get_score(0))
        s.set_sight(0, 39, 12)
        self.assertEqual((39, 12, None), s.get_sight(0))

        with self.assertRaises(Exception):
            s.get_sight(-1)
        with self.assertRaises(Exception):
            s.get_sight(12)
        with self.assertRaises(Exception):
            s.get_sight(0.5)

        basic_sights = Sights(5)
        for i, s in enumerate(basic_sights):
            x, y, score = s
            x += i + 10
            y += i + 20
            basic_sights.set_sight(i, x, y)

    # ------------------------------------------------------------------------

    def test_overloads(self):
        s = Sights(68)
        self.assertEqual((-1, -1, None), s[0])
        self.assertEqual((-1, -1, None), s[0])
        # with slice:
        self.assertEqual([(-1, -1, None)]*10, s[0:10])

        for item in s:
            self.assertEqual((-1, -1, None), item)

        s.set_sight(1, 10, 20)
        self.assertTrue((10, 20) in s)
        self.assertTrue((10, 20, 0.123) in s)
        self.assertFalse((10, 10) in s)

    # ------------------------------------------------------------------------

    def test_get_list(self):
        s = Sights(5)
        s.set_sight(0, 10, 20)

        x = s.get_x()
        self.assertEqual(5, len(x))
        self.assertTrue(isinstance(x, tuple))
        self.assertEqual(10, x[0])
        self.assertEqual((10, 20, None), s[0])

        # we expect that if we modify 'x', it won't change 's'
        x = list(x)
        x[0] = "anything"
        self.assertEqual("anything", x[0])
        self.assertEqual((10, 20, None), s[0])

# ---------------------------------------------------------------------------


class TestImageFaceLandmark(unittest.TestCase):

    def test_load_resources(self):
        fl = ImageFaceLandmark()
        self.assertEqual(0, len(fl))
        with self.assertRaises(IOError):
            fl.load_model("toto.txt", "toto")

        fl.load_model(MODEL_LBF68, MODEL_DAT)
        with self.assertRaises(Exception):
            fl.load_model(NET, MODEL_LBF68)

    # ------------------------------------------------------------------------

    def test_contains(self):
        fd = ImageFaceLandmark()
        # access to the private list of landmarks and set a point
        fd._ImageFaceLandmark__sights.set_sight(0, 124, 235)
        self.assertTrue((124, 235, None) in fd)
        self.assertFalse((24, 35, None) in fd)
        self.assertTrue((124, 235) in fd)
        self.assertTrue([124, 235, 0, 0] in fd)
        self.assertFalse((24, 35, 0, 0) in fd)

    # ------------------------------------------------------------------------

    def test_mark_nothing(self):
        fl = ImageFaceLandmark()
        fl.load_model(MODEL_DAT)

        # The image we'll work on
        fn = os.path.join(DATA, "Slovenia2016Sea.jpg")
        with self.assertRaises(TypeError):
            fl.detect_sights(fn, sppasCoords(0, 0, 0, 0))
        img = sppasImage(filename=fn)

        # Nothing should be marked. No face in the image
        with self.assertRaises(Exception):
            fl.detect_sights(img, sppasCoords(0, 0, 100, 100))

    # ------------------------------------------------------------------------

    def test_basic_sights(self):
        fn = os.path.join(DATA, "BrigitteBigiSlovenie2016-portrait.jpg")
        img = sppasImage(filename=fn)

        fd = ImageFaceDetection()
        fd.load_model(HAAR2)
        fd.detect(img)
        coords = fd.get_best()

        empirical = ImageFaceLandmark.basic_sights(img, coords)

        fn = os.path.join(DATA, "BrigitteBigiSlovenie2016-sights.jpg")
        w = sppasCoordsImageWriter()
        w.set_options(tag=True)
        w.write(img, [[c for c in empirical]], fn)

    # ------------------------------------------------------------------------

    def test_mark_normal(self):
        fd = ImageFaceDetection()
        fd.load_model(HAAR2)
        fl = ImageFaceLandmark()
        fl.load_model(MODEL_LBF68, MODEL_DAT)

        # The image we'll work on
        fn = os.path.join(DATA, "BrigitteBigiSlovenie2016-portrait.jpg")
        img = sppasImage(filename=fn)
        fd.detect(img)
        coords = fd.get_best()
        fl.detect_sights(img, coords)

        fn = os.path.join(DATA, "BrigitteBigiSlovenie2016-sights.jpg")
        w = sppasCoordsImageWriter()
        w.set_options(tag=True)
        w.write(img, [[c for c in fl]], fn)

    # ------------------------------------------------------------------------

    def test_mark_montage(self):
        fl = ImageFaceLandmark()
        fl.load_model(MODEL_LBF68, MODEL_DAT)

        # The image we'll work on, with 3 faces to be detected
        fn = os.path.join(DATA, "montage.png")
        img = sppasImage(filename=fn)

        fd = ImageFaceDetection()
        fd.load_model(HAAR1, HAAR2, NET)
        fd.detect(img)
        self.assertEqual(len(fd), 3)

        w = sppasCoordsImageWriter()
        w.set_options(tag=True)
        for i, coord in enumerate(fd):
            fn = os.path.join(DATA, "montage_{:d}-face.jpg".format(i))
            # Create an image of the ROI
            cropped_face = img.icrop(coord)
            cropped_face.write(fn)
            try:
                fn = os.path.join(DATA, "montage_{:d}-sights.jpg".format(i))
                fl.detect_sights(cropped_face, sppasCoords(0, 0, coord.w, coord.h))
                w.write(cropped_face, [[c for c in fl]], fn)

            except Exception as e:
                print("Error for coords {}: {}".format(i, str(e)))

# ---------------------------------------------------------------------------


class TestVideoFaceLandmark(unittest.TestCase):

    VIDEO = os.path.join(paths.samples, "faces", "video_sample.mp4")

    # -----------------------------------------------------------------------

    def test_detect(self):
        fld = ImageFaceDetection()
        fld.load_model(NET)
        fli = ImageFaceLandmark()
        fli.load_model(MODEL_LBF68, MODEL_DAT)

        # no valid faces
        flv = VideoFaceLandmark(fli)
        with self.assertRaises(Exception):
            flv.video_face_sights(TestVideoFaceLandmark.VIDEO)
        with self.assertRaises(Exception):
            flv.video_face_sights(TestVideoFaceLandmark.VIDEO, csv_faces="toto.csv")

        flv = VideoFaceLandmark(fli, fld)
        results = flv.video_face_sights(TestVideoFaceLandmark.VIDEO)


