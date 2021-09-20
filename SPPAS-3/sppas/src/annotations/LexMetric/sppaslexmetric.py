# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.LexMetric.sppaslexmetric.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: SPPAS integration of the LexMetric automatic annotation.

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

import logging

from sppas.src.utils import sppasUnicode
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel

from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyOutputError
from ..baseannot import sppasBaseAnnotation
from ..annotationsexc import AnnotationOptionError
from .occrank import OccRank

# ----------------------------------------------------------------------------


class sppasLexMetric(sppasBaseAnnotation):
    """SPPAS integration of the occ and rank estimator.

    """

    def __init__(self, log=None):
        """Create a new sppasLexMetric instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasLexMetric, self).__init__("lexmetric.json", log)

        # List of the tags to create segments
        self._separators = ['#', '+', 'dummy']

    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: list of sppasOption instances

        """
        for opt in options:

            key = opt.get_key()

            if "alt" == key:
                self.set_alt(opt.get_value())

            elif "tiername" == key:
                self.set_tiername(opt.get_value())

            elif "separators" == key:
                self.set_segments_separators(opt.get_value())

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_alt(self, alt):
        """Fix the alt option, used to estimate occ and rank.

        :param alt: (bool)

        """
        self._options['alt'] = bool(alt)

    # -----------------------------------------------------------------------

    def set_tiername(self, tier_name):
        """Fix the tiername option.

        :param tier_name: (str)

        """
        self._options['tiername'] = sppasUnicode(tier_name).to_strip()

    # -----------------------------------------------------------------------

    def set_segments_separators(self, entry):
        """Fix the separators to create segments.

        :param entry: (str) Entries separated by whitespace.

        """
        sp = sppasUnicode(entry)
        tg = sp.to_strip()
        if len(tg) > 0:
            self._separators = tg.split()
        else:
            self._separators = list()

    # ----------------------------------------------------------------------
    # Annotate
    # ----------------------------------------------------------------------

    def tier_to_segment_occ(self, input_tier):
        """Create segment intervals and eval the number of occurrences.

        :param input_tier: (sppasTier)
        :returns: (sppasTier)

        """
        if len(self._separators) > 0:
            occ_ann = input_tier.export_to_intervals(self._separators)
        else:
            occ_ann = input_tier.copy()
            occ_ann.gen_id()
        occ_ann.set_name("LM-OccAnnInSegments")

        occ_lab = occ_ann.copy()
        occ_lab.gen_id()
        occ_lab.set_name("LM-OccLabInSegments")

        for tg1, tg2 in zip(occ_ann, occ_lab):
            values_anns = input_tier.find(tg1.get_lowest_localization(), tg1.get_highest_localization())
            tg1.set_labels([sppasLabel(sppasTag(str(len(values_anns)), "int"))])

            nbl = 0
            for a in values_anns:
                nbl += len(a.get_labels())
            tg2.set_labels([sppasLabel(sppasTag(str(nbl), "int"))])

        return occ_ann, occ_lab

    # ----------------------------------------------------------------------

    def get_input_tier(self, input_files):
        """Return the input tier from the inputs.

        :param input_files: (list)

        """
        for filename in input_files:
            parser = sppasTrsRW(filename)
            trs_input = parser.read()
            tier_spk = trs_input.find(self._options['tiername'], case_sensitive=False)
            if tier_spk is not None:
                return tier_spk

        logging.error("Tier with name '{:s}' not found in input file."
                      "".format(self._options['tiername']))
        raise NoTierInputError

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        :param input_file: (list of str) time-aligned tokens, or other
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get the tier to be used
        tier = self.get_input_tier(input_file)

        # Evaluate
        ocrk = OccRank(tier)
        occ_tier = ocrk.occ()
        rank_tier = ocrk.rank()
        sgmt_occ_ann_tier, sgmt_occ_lab_tier = self.tier_to_segment_occ(tier)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('token_lexmetric_result_of', input_file[0])
        trs_output.append(occ_tier)
        trs_output.append(rank_tier)
        trs_output.append(sgmt_occ_ann_tier)
        trs_output.append(sgmt_occ_lab_tier)

        # Save in a file
        if output is not None:
            if len(trs_output) > 0:
                output_file = self.fix_out_file_ext(output)
                parser = sppasTrsRW(output_file)
                parser.write(trs_output)
                return [output_file]
            else:
                raise EmptyOutputError

        return trs_output

    # ----------------------------------------------------------------------

    def get_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-lexm")

    def get_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputpattern", "")
