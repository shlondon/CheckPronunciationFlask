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

    src.files.tests.test_filedatafilters.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import unittest
import os

from sppas.src.config import paths
from sppas.src.utils import u
from ..workspace import sppasWorkspace
from ..filedatacompare import *
from ..filedatafilters import sppasFileDataFilters
from ..filestructure import FileRoot

# ---------------------------------------------------------------------------


class TestsFileDataFilter (unittest.TestCase):

    def setUp(self):
        f1 = os.path.join(paths.samples, 'samples-fra', 'AC track_0379.PitchTier')
        f2 = os.path.join(paths.samples, 'samples-jpn', 'JPA_M16_JPA_T02.TextGrid')
        f3 = os.path.join(paths.samples, 'samples-cat', 'TB-FE1-H1_phrase1.TextGrid')

        self.files = sppasWorkspace()
        self.files.add_file(__file__)
        self.files.add_file(f1)
        self.files.add_file(f2)
        self.files.add_file(f3)

        ref1 = sppasCatReference('spk1')
        ref1.set_type('SPEAKER')
        ref1.append(sppasRefAttribute('age', '20', "int"))
        ref1.append(sppasRefAttribute('name', 'toto'))
        ref1.append(sppasRefAttribute('gender', 'male'))

        ref2 = sppasCatReference('record')
        ref2.append(sppasRefAttribute('age', '50', "int"))
        ref2.append(sppasRefAttribute('name', 'toto'))

        ref3 = sppasCatReference('whatever')
        ref3.append(sppasRefAttribute('gender', 'female'))

        fr1 = self.files.get_object(FileRoot.root(f1))
        fr1.add_ref(ref1)

        fr2 = self.files.get_object(FileRoot.root(f3))
        fr2.add_ref(ref2)
        fr2.add_ref(ref3)

        self.data_filter = sppasFileDataFilters(self.files)

    def test_path(self):
        self.assertEqual(3, len(self.data_filter.path(contains=u('samples-'))))

    def test_root(self):
        self.assertEqual(4, len(self.data_filter.root(contains=u('_'))))

    def test_filename(self):
        self.assertEqual(1, len(self.data_filter.name(iexact=u('jpa_m16_jpa_t02'))))

    def test_filename_extension(self):
        self.assertEqual(3, len(self.data_filter.extension(not_exact=u('.PY'))))

    def test_filename_state(self):
        self.assertEqual(4, len(self.data_filter.file(state=States().UNUSED)))

    def test_ref_id(self):
        self.assertEqual(1, len(self.data_filter.ref(startswith=u('rec'))))
        self.assertEqual(0, len(self.data_filter.ref(startswith=u('aa'))))
        self.assertEqual(2, len(self.data_filter.ref(not_startswith=u('aa'))))
        # test with "not_":
        self.assertEqual(2, len(self.data_filter.ref(not_startswith=u('rec'))))
        # it's 2 because:
        #  - fr1 has ref1 which does not starts with "rec" so it returns true to the filter;
        #  - fr2 has 2 references:
        #       * ref2 returns false to the filter (to not select this root) but
        #       * ref3 returns true to the filter because it does not starts with "rec".
        # so fr2 is also selected because at least one of its ref returned true.

    def test_att(self):
        self.assertEqual(1, len(self.data_filter.att(iequal=('age', '20'))))
        self.assertEqual(1, len(self.data_filter.att(gt=('age', '30'))))
        self.assertEqual(2, len(self.data_filter.att(le=('age', '60'))))
        self.assertEqual(2, len(self.data_filter.att(exact=('name', 'toto'))))
        self.assertEqual(2, len(self.data_filter.att(exact=('name', 'toto'), lt=('age', '60'), logic_bool="and")))
        self.assertEqual(1, len(self.data_filter.att(exact=('name', 'toto'), equal=('age', '20'), logic_bool="and")))
        self.assertEqual(2, len(self.data_filter.att(exact=('name', 'toto'), equal=('age', '20'), logic_bool="or")))

    def test_mixed_filter_sets_way(self):
        self.assertEqual(1, len(self.data_filter.extension(not_exact=u('.PY')) &
                                self.data_filter.name(iexact=u('jpa_m16_jpa_t02'))))

    def test_mixed_filter_argument_way(self):
        self.assertEqual(2, len(self.data_filter.extension(not_exact=u('.PY'), startswith=u('.TEXT'), logic_bool='and')))

    def test_extended(self):
        files = sppasWorkspace()
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P8.wav'))
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P8.TextGrid'))
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P9.wav'))
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P9.TextGrid'))
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_C006-P6.wav'))
        files.add_file(os.path.join(paths.samples, 'samples-fra', 'F_F_C006-P6.TextGrid'))
        files.add_file(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T02.wav'))
        files.add_file(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T02.PitchTier'))
        files.add_file(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T33.wav'))
        files.add_file(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T33.PitchTier'))

        rf = sppasCatReference('corpus-fra')
        rf.set_type('STANDALONE')

        re = sppasCatReference('corpus-eng')
        re.set_type('STANDALONE')

        spk1 = sppasCatReference('SPK-B003')
        spk1.set_type('SPEAKER')
        spk1.append(sppasRefAttribute('gender', 'male', "str"))
        spk1.append(sppasRefAttribute('lang', 'fra', "str"))

        spk2 = sppasCatReference('SPK-C006')
        spk2.set_type('SPEAKER')
        spk2.append(sppasRefAttribute('gender', 'female', "str"))
        spk2.append(sppasRefAttribute('lang', 'fra', "str"))

        spk3 = sppasCatReference('SPK-M15')
        spk3.set_type('SPEAKER')
        spk3.append(sppasRefAttribute('gender', 'male', "str"))
        spk3.append(sppasRefAttribute('lang', 'eng', "str"))

        fr1 = files.get_object(FileRoot.root(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P8.wav')))
        fr1.add_ref(rf)
        fr1.add_ref(spk1)

        fr2 = files.get_object(FileRoot.root(os.path.join(paths.samples, 'samples-fra', 'F_F_B003-P9.wav')))
        fr2.add_ref(rf)
        fr2.add_ref(spk1)

        fr3 = files.get_object(FileRoot.root(os.path.join(paths.samples, 'samples-fra', 'F_F_C006-P6.wav')))
        fr3.add_ref(rf)
        fr3.add_ref(spk2)

        fr4 = files.get_object(FileRoot.root(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T02.wav')))
        fr4.add_ref(spk3)
        fr4.add_ref(re)

        fr5 = files.get_object(FileRoot.root(os.path.join(paths.samples, 'samples-eng', 'ENG_M15_ENG_T33.wav')))
        fr5.add_ref(spk3)
        fr5.add_ref(re)

        data_filter = sppasFileDataFilters(files)
        # Test references
        self.assertEqual(6, len(data_filter.ref(contains=u('fra'))))
        self.assertEqual(0, len(data_filter.ref(startswith=u('aa'))))
        self.assertEqual(10, len(data_filter.ref(not_startswith=u('aa'))))

        # because the roots have more than one ref:
        self.assertEqual(10, len(data_filter.ref(not_contains=u('fra'))))

        # Test attributes
        self.assertEqual(8, len(data_filter.att(exact=('gender', 'male'))))
        self.assertEqual(2, len(data_filter.att(exact=('gender', 'female'))))
        self.assertEqual(8, len(data_filter.att(not_exact=('gender', 'female'))))
        self.assertEqual(8, len(data_filter.att(iexact=('gender', 'MALE'))))
        self.assertEqual(2, len(data_filter.att(iexact=('gender', 'FEMALE'))))
        self.assertEqual(10, len(data_filter.att(contains=('gender', 'male'))))
        self.assertEqual(0, len(data_filter.att(not_contains=('gender', 'male'))))
        self.assertEqual(4, len(data_filter.att(exact=('gender', 'male'), iexact=("lang", "fra"), logic_bool="and")))
        self.assertEqual(4, len(data_filter.att(exact=('gender', 'male')) & data_filter.att(exact=("lang", "fra"))))
