# -*- coding:utf-8 -*-
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

    src.files.tests.test_fileref.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import unittest

from sppas.src.config import sppasTypeError
from sppas.src.utils import u
from sppas.src.wkps.fileref import sppasCatReference, sppasRefAttribute
from sppas.src.wkps.filebase import States
from ..wkpexc import AttributeIdValueError, AttributeTypeValueError

# ---------------------------------------------------------------------------


class TestAttribute(unittest.TestCase):

    def setUp(self):
        self.valint = sppasRefAttribute('age', '12', 'int', 'speaker\'s age')
        self.valfloat = sppasRefAttribute('freq', '0.002', 'float', 'word appearance frequency')
        self.valbool = sppasRefAttribute('adult', 'false', 'bool', 'speaker is minor')
        self.valstr = sppasRefAttribute('utf', 'Hi everyone !', None, u('первый токен'))

    # ---------------------------------------------------------------------------

    def test_int(self):
        self.assertTrue(isinstance(self.valint.get_typed_value(), int))
        self.assertEqual('12', self.valint.get_value())

    # ---------------------------------------------------------------------------

    def test_float(self):
        self.assertTrue(isinstance(self.valfloat.get_typed_value(), float))
        self.assertNotEqual(0.002, self.valfloat.get_value())

    # ---------------------------------------------------------------------------

    def test_bool(self):
        self.assertFalse(self.valbool.get_typed_value())

    # ---------------------------------------------------------------------------

    def test_str(self):
        self.assertEqual('Hi everyone !', self.valstr.get_typed_value())
        self.assertEqual('Hi everyone !', self.valstr.get_value())

    # ---------------------------------------------------------------------------

    def test_repr(self):
        self.assertEqual(u('age, 12, speaker\'s age'), str(self.valint))

    # ---------------------------------------------------------------------------

    def test_set_type_value(self):
        with self.assertRaises(sppasTypeError) as error:
            self.valbool.set_value_type('sppasRefAttribute')

        self.assertTrue(isinstance(error.exception, sppasTypeError))

    # ---------------------------------------------------------------------------

    def test_get_valuetype(self):
        self.assertEqual('str', self.valstr.get_value_type())

    # ---------------------------------------------------------------------------

    def test_dynamic_sets(self):
        att = sppasRefAttribute("age")

        with self.assertRaises(AttributeTypeValueError):
            att.set_value_type("int")

        att.set_value("12")
        self.assertEqual("12", att.get_typed_value())
        att.set_value_type("int")
        self.assertEqual('int', att.get_value_type())
        self.assertEqual(12, att.get_typed_value())
        self.assertEqual("12", att.get_value())

# ---------------------------------------------------------------------------


class TestReferences(unittest.TestCase):

    def setUp(self):
        self.micros = sppasCatReference('microphone')
        self.att = sppasRefAttribute('mic1', 'Bird UM1', None, '最初のインタビューで使えていましたマイク')
        self.micros.append(self.att)
        self.micros.add('mic2', 'AKG D5')

    # ---------------------------------------------------------------------------

    def test_get_item(self):
        self.assertEqual(u('最初のインタビューで使えていましたマイク'),
                         self.micros.att('mic1').get_description())

    # ---------------------------------------------------------------------------

    def test_sppas_ref_attribute(self):
        self.assertFalse(isinstance(self.micros.att('mic2').get_typed_value(), int))

    # ---------------------------------------------------------------------------

    def test_add_key(self):
        with self.assertRaises(ValueError) as AsciiError:
            self.micros.add('i', 'Blue Yeti')

        self.assertTrue(isinstance(AsciiError.exception, ValueError))

    # ---------------------------------------------------------------------------

    def test_pop_key(self):
        self.micros.pop('mic1')
        self.assertEqual(1, len(self.micros))
        self.micros.append(self.att)
        self.micros.pop(self.att)
        self.assertEqual(1, len(self.micros))


