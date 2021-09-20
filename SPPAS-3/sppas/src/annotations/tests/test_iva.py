# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.tests.test_iva.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Test of IVA auto annotation.

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
import os.path

from ..IVA import sppasIVA
from ..IVA import IntervalValuesAnalysis
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasLocation, sppasInterval, sppasPoint

# ---------------------------------------------------------------------------

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --------------------------------------------------------------------------


class TestIVA(unittest.TestCase):

    def setUp(self):
        self.iva_items = dict()
        self.iva_items["sgmt_1"] = [0.1, 0.2, 0.3]  # deceleration
        self.iva_items["sgmt_2"] = [0.1, 0.3, 0.2]  # deceleration then acceleration
        self.iva_items["sgmt_3"] = [0.3, 0.2, 0.1]  # acceleration

    # -----------------------------------------------------------------------

    def test_iva_estimator(self):
        ts = IntervalValuesAnalysis(self.iva_items)

        self.assertEqual(len(self.iva_items), len(ts.len()))
        self.assertEqual(3, ts.len()["sgmt_1"])  # nb of occurrences of 1st segment
        self.assertEqual(3, ts.len()["sgmt_2"])
        self.assertEqual(3, ts.len()["sgmt_3"])

        self.assertEqual(0.6, ts.total()["sgmt_1"])  # total duration of 1st segment
        self.assertEqual(0.6, ts.total()["sgmt_2"])
        self.assertEqual(0.6, ts.total()["sgmt_3"])

        self.assertEqual(0.2, round(ts.mean()["sgmt_1"], 2))  # mean duration of 1st segment
        self.assertEqual(0.2, round(ts.mean()["sgmt_2"], 2))
        self.assertEqual(0.2, round(ts.mean()["sgmt_3"], 2))

        self.assertEqual(0.2, round(ts.median()["sgmt_1"], 2))  # median duration of 1st segment
        self.assertEqual(0.3, round(ts.median()["sgmt_2"], 2))
        self.assertEqual(0.2, round(ts.median()["sgmt_3"], 2))

        # stdev = sqrt(variance) ; variance = sum(value-mean)^2 / N
        # the use of N = for a population, not a sample (with N-1).
        self.assertEqual(0.0816, round(ts.stdev()["sgmt_1"], 4))  # stdev duration of tg1
        self.assertEqual(0.0816, round(ts.stdev()["sgmt_2"], 4))
        self.assertEqual(0.0816, round(ts.stdev()["sgmt_3"], 4))

        # linear regression
        self.assertEqual(0.1, round(ts.intercept_slope()["sgmt_1"][0], 2))  # intercept
        self.assertEqual(0.1, round(ts.intercept_slope()["sgmt_1"][1], 2))  # slope
        self.assertEqual(0.15, round(ts.intercept_slope()["sgmt_2"][0], 2))
        self.assertEqual(0.05, round(ts.intercept_slope()["sgmt_2"][1], 2))
        self.assertEqual(0.3, round(ts.intercept_slope()["sgmt_3"][0], 2))
        self.assertEqual(-0.1, round(ts.intercept_slope()["sgmt_3"][1], 2))

    # -----------------------------------------------------------------------

    def test_tier_iva(self):
        tier = sppasTier("tier")
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(0., 0.), sppasPoint(1., 0.0))),
                               sppasLabel(sppasTag('#')))
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(1., 0.), sppasPoint(2., 0.01))),
                               sppasLabel(sppasTag('toto')))
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(3., 0.01), sppasPoint(4., 0.01))),
                               sppasLabel(sppasTag('titi')))
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(4., 0.01), sppasPoint(5., 0.01))))
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(5., 0.01), sppasPoint(6.5, 0.005))),
                               sppasLabel(sppasTag('toto')))
        tier.create_annotation(sppasLocation(sppasInterval(sppasPoint(6.5, 0.005), sppasPoint(9.5, 0.))),
                               sppasLabel(sppasTag('toto')))

        tier_values = sppasTier("PitchTier")
        tier_values.create_annotation(sppasLocation(sppasPoint(1.)), sppasLabel(sppasTag("180", "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(1.5)), sppasLabel(sppasTag("200", "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(3.)), sppasLabel(sppasTag("100", "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(3.5)), sppasLabel(sppasTag(150, "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(5.5)), sppasLabel(sppasTag(400, "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(6.5)), sppasLabel(sppasTag(300, "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(7.5)), sppasLabel(sppasTag(350, "int")))
        tier_values.create_annotation(sppasLocation(sppasPoint(8.5)), sppasLabel(sppasTag(250, "int")))

        # test the created segments tier
        tg = sppasIVA().tier_to_segments(tier)
        self.assertEqual(3, len(tg))
        # to be tested:
        #  [1., 2.] tg_1
        #  [3.; 4.] tg_2
        #  [5.; 9.5] tg_3

        tg_dur, ts = sppasIVA().tier_to_labelled_segments(tg, tier_values)
        self.assertEqual(3, len(ts))
        self.assertEqual(3, len(tg_dur))
        self.assertEqual([180, 200], tg_dur['sgmt_1'])
        self.assertEqual([100, 150], tg_dur['sgmt_2'])
        self.assertEqual([400, 300, 350, 250], tg_dur['sgmt_3'])

        iva = IntervalValuesAnalysis(tg_dur)

        occurrences = iva.len()
        self.assertEqual(2, occurrences['sgmt_1'])
        self.assertEqual(2, occurrences['sgmt_2'])
        self.assertEqual(4, occurrences['sgmt_3'])

        mean = iva.mean()
        self.assertEqual(190., mean['sgmt_1'])
        self.assertEqual(125., mean['sgmt_2'])
        self.assertEqual(325, mean['sgmt_3'])
