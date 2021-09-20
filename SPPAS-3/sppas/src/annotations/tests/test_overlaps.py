"""
:filename: sppas.src.annotations.tests.test_overlaps.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Package for the configuration of SPPAS.

.. _This file is part of SPPAS: http://www.sppas.org/
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

import unittest

from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasPoint
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from ..Overlaps.overspeech import OverActivity


class TestOverActivity(unittest.TestCase):

    def test_init(self):
        o = OverActivity()
        self.assertTrue(isinstance(o, OverActivity))
        self.assertEqual(0, len(o))

        with self.assertRaises(TypeError):
            OverActivity([1, 2, 3])

        o = OverActivity((sppasTag("#"), sppasTag("+")))
        self.assertEqual(2, len(o))

    def test_overlap_errors(self):
        o = OverActivity((sppasTag("#"), sppasTag("+")))

        # Expect two sppasTier instances
        with self.assertRaises(TypeError):
            o.overlaps(1, 2)

        # Expect two non-empty tiers
        t1 = sppasTier("t1")
        t2 = sppasTier("t2")
        with self.assertRaises(IOError):
            o.overlaps(t1, t2)

        # Expect two interval tiers
        t1.create_annotation(sppasLocation(sppasPoint(1)))
        t2.create_annotation(sppasLocation(sppasPoint(1)))
        with self.assertRaises(TypeError):
            o.overlaps(t1, t2)

        # Expect a single label in annotations
        t1 = sppasTier("t1")
        t2 = sppasTier("t2")
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(1), sppasPoint(2))),
                             [sppasLabel(sppasTag("a")), sppasLabel(sppasTag("b"))])
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(1), sppasPoint(3))))
        with self.assertRaises(ValueError):
            o.overlaps(t1, t2)

    def test_overlap(self):
        o = OverActivity((sppasTag("#"), sppasTag("+")))
        t1 = sppasTier("t1")
        t2 = sppasTier("t2")
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(1), sppasPoint(2))))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(1), sppasPoint(3))))

        # ignore the non-labelled intervals
        tier = o.overlaps(t1, t2)
        self.assertEqual(0, len(tier))

        # normal situation: contains
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(2), sppasPoint(5))),
                             sppasLabel(sppasTag("speech")))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(3), sppasPoint(4))),
                             sppasLabel(sppasTag("speech")))
        tier = o.overlaps(t1, t2)
        self.assertEqual(1, len(tier))
        self.assertEqual(sppasPoint(3), tier[0].get_lowest_localization())
        self.assertEqual(sppasPoint(4), tier[0].get_highest_localization())

        # normal situation: during
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(6), sppasPoint(7))),
                             sppasLabel(sppasTag("speech")))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(5), sppasPoint(8))),
                             sppasLabel(sppasTag("speech")))
        tier = o.overlaps(t1, t2)
        self.assertEqual(2, len(tier))
        self.assertEqual(sppasPoint(6), tier[1].get_lowest_localization())
        self.assertEqual(sppasPoint(7), tier[1].get_highest_localization())

        # normal situation: overlaps
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(8), sppasPoint(10))),
                             sppasLabel(sppasTag("speech")))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(9), sppasPoint(11))),
                             sppasLabel(sppasTag("speech")))
        tier = o.overlaps(t1, t2)
        self.assertEqual(3, len(tier))
        self.assertEqual(sppasPoint(9), tier[2].get_lowest_localization())
        self.assertEqual(sppasPoint(10), tier[2].get_highest_localization())

        # normal situation: overlapped by
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(12), sppasPoint(14))),
                             sppasLabel(sppasTag("laughter")))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(11), sppasPoint(13))),
                             sppasLabel(sppasTag("laughter")))
        tier = o.overlaps(t1, t2)
        self.assertEqual(4, len(tier))
        self.assertEqual(sppasPoint(12), tier[3].get_lowest_localization())
        self.assertEqual(sppasPoint(13), tier[3].get_highest_localization())

        # normal situation: empty label overlapped
        t1.create_annotation(sppasLocation(sppasInterval(sppasPoint(14), sppasPoint(15))),
                             sppasLabel(sppasTag("speech")))
        t2.create_annotation(sppasLocation(sppasInterval(sppasPoint(14), sppasPoint(15))))
        tier = o.overlaps(t1, t2)
        self.assertEqual(4, len(tier))

