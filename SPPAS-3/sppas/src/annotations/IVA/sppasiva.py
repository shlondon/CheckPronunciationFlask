# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.IVA.sppasiva.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the IVA automatic annotation.

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

from sppas.src.utils.makeunicode import sppasUnicode
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata.aio.aioutils import serialize_labels

from ..baseannot import sppasBaseAnnotation
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoTierInputError
from ..annotationsexc import BadInputError
from ..annotationsexc import EmptyOutputError

from .intervalvaluesanalysis import IntervalValuesAnalysis

# ----------------------------------------------------------------------------


class sppasIVA(sppasBaseAnnotation):
    """Estimate IVA on a tier.

    Get or create segments then map them into a dictionary where:

        - key is a label assigned to the segment;
        - value is the list of observed values in the segment.

    """

    def __init__(self, log=None):
        """Create a new sppasIVA instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasIVA, self).__init__("iva.json", log)

        # List of the tags to create segments
        self._separators = ['#', '+', '*', '@', 'dummy']

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if "iva_prefix_label" == key:
                self.set_sgmt_prefix_label(opt.get_value())

            elif "values" == key:
                self.set_input_tiername_values(opt.get_value())

            elif "segments" == key:
                self.set_input_tiername_segments(opt.get_value())

            elif "separators" == key:
                self.set_segments_separators(opt.get_value())

            elif "occ" == key:
                self.set_eval(occ=opt.get_value())

            elif "total" == key:
                self.set_eval(total=opt.get_value())

            elif "mean" == key:
                self.set_eval(mean=opt.get_value())

            elif "median" == key:
                self.set_eval(median=opt.get_value())

            elif "stdev" == key:
                self.set_eval(stdev=opt.get_value())

            elif "linreg" == key:
                self.set_eval(linreg=opt.get_value())

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_sgmt_prefix_label(self, prefix):
        """Fix the prefix to add to each segment.

        :param prefix: (str) Default is 'sgmt_'

        """
        sp = sppasUnicode(prefix)
        tg = sp.to_strip()
        if len(tg) > 0:
            self._options['iva_prefix_label'] = tg

    # -----------------------------------------------------------------------

    def set_input_tiername_values(self, tiername):
        """Fix the name of the tier with values.

        :param tiername: (str) Default is 'PitchTier'

        """
        sp = sppasUnicode(tiername)
        tg = sp.to_strip()
        if len(tg) > 0:
            self._options['values'] = tg

    # -----------------------------------------------------------------------

    def set_input_tiername_segments(self, tiername):
        """Fix the name of the tier with segments.

        :param tiername: (str) Default is 'TokensAlign'

        """
        sp = sppasUnicode(tiername)
        tg = sp.to_strip()
        if len(tg) > 0:
            self._options['segments'] = tg

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

    # -----------------------------------------------------------------------

    def set_eval(self, occ=None, total=None, mean=None, median=None, stdev=None, linreg=None):
        """Set IVA evaluations to perform.

        :param total: (bool) Estimates total of values in segments.
        :param mean: (bool) Estimates mean of values in segments.
        :param median: (bool) Estimates median of values in segments.
        :param stdev: (bool) Estimates standard deviation of values in segments.
        :param linreg: (bool) Estimates linear regression of values in segments.

        """
        if occ is not None:
            self._options['occ'] = bool(occ)
        if total is not None:
            self._options['total'] = bool(total)
        if mean is not None:
            self._options['mean'] = bool(mean)
        if median is not None:
            self._options['median'] = bool(median)
        if stdev is not None:
            self._options['stdev'] = bool(stdev)
        if linreg is not None:
            self._options['linreg'] = bool(linreg)

    # -----------------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------------

    def tier_to_segments(self, input_tier):
        """Create segment intervals.

        :param input_tier: (sppasTier)
        :returns: (sppasTier)

        """
        if len(self._separators) > 0:
            intervals = input_tier.export_to_intervals(self._separators)
        else:
            intervals = input_tier.copy()
        intervals.set_name("IVA-Segments")

        for i, tg in enumerate(intervals):
            tag_str = self._options['iva_prefix_label']
            tag_str += str(i+1)
            tg.set_labels([sppasLabel(sppasTag(tag_str))])

        return intervals

    # ----------------------------------------------------------------------

    def tier_to_labelled_segments(self, segments, input_tier_values):
        """Create the segment intervals within the values.

        :param segments: (sppasTier) segment intervals to get values
        :param input_tier_values: (sppasTier) tags are float/int values
        :returns: (dict, sppasTier) dict of segment/values, labelled segments

        """
        intervals_tier = segments.copy()
        intervals_tier.gen_id()
        intervals_tier.set_name("IVA-Values")
        for i, tg in enumerate(intervals_tier):
            tg.set_labels(None)

        iva_items = dict()

        for i, tg in enumerate(intervals_tier):
            iva_ann = segments[i]
            iva_label = serialize_labels(iva_ann.get_labels())

            values_anns = input_tier_values.find(tg.get_lowest_localization(), tg.get_highest_localization())
            all_labels = list()
            for ann in values_anns:
                ann_labels = ann.get_labels()
                all_labels.extend(ann_labels)
            tg.set_labels(all_labels)

            # Append in the list of values of this IVA
            iva_items[iva_label] = list()
            for label in all_labels:
                for tag, score in label:
                    ttag = tag.get_typed_content()
                    iva_items[iva_label].append(ttag)

        return iva_items, intervals_tier

    # -----------------------------------------------------------------------

    @staticmethod
    def iva_to_tier(iva_result, sgmts_tier, tier_name, tag_type="float"):
        """Create a tier from one of the IVA result (mean, sd, ...).

        :param iva_result: One of the results of TGA
        :param sgmts_tier: (sppasTier) Tier with the segments
        :param tier_name: (str) Name of the output tier
        :param tag_type: (str) Type of the sppasTag to be included

        :returns: (sppasTier)

        """
        tier = sppasTier(tier_name)

        for iva_ann in sgmts_tier:
            iva_label = serialize_labels(iva_ann.get_labels())
            tag_value = iva_result[iva_label]
            if tag_type == "float":
                tag_value = round(tag_value, 5)

            tier.create_annotation(
                iva_ann.get_location().copy(),
                sppasLabel(sppasTag(tag_value, tag_type)))

        return tier

    # ----------------------------------------------------------------------

    @staticmethod
    def iva_to_tier_reglin(iva_result, sgmts_tier, intercept=True):
        """Create tiers of intercept,slope from the IVA result.

        :param iva_result: intercept,slope result of IVA
        :param sgmts_tier: (sppasTier) Tier with the segments
        :param intercept: (boolean) Export the intercept.
        If False, export Slope.

        :returns: (sppasTier)

        """
        if intercept is True:
            tier = sppasTier('IVA-Intercept')
        else:
            tier = sppasTier('IVA-Slope')

        for iva_ann in sgmts_tier:
            iva_label = serialize_labels(iva_ann.get_labels())
            loc = iva_ann.get_location().copy()
            if intercept is True:
                tag_value = iva_result[iva_label][0]
            else:
                tag_value = iva_result[iva_label][1]

            tag_value = round(tag_value, 5)
            tier.create_annotation(loc, sppasLabel(sppasTag(tag_value, "float")))

        return tier

    # ----------------------------------------------------------------------

    def convert(self, input_tier_values, input_tier_segments):
        """Estimate IVA on the given input tier with values.

        :param input_tier_values: (sppasTier) Tier with numerical values.
        :param input_tier_segments: (sppasTier) Tier with intervals.
        :returns: (sppasTranscription)

        """
        trs_out = sppasTranscription("IntervalValuesAnalysis")

        # Create the segments: intervals between separators
        segments = self.tier_to_segments(input_tier_segments)
        segments.set_meta('segments_of_tier', input_tier_segments.get_name())
        trs_out.append(segments)

        # Create the segments labelled with the values and values' items
        iva_items, val_segs_tier = self.tier_to_labelled_segments(segments, input_tier_values)
        trs_out.append(val_segs_tier)

        # Estimate IVA on items of the dict
        ts = IntervalValuesAnalysis(iva_items)

        # Put IVA results into tiers
        if self._options['occ'] is True:
            tier = sppasIVA.iva_to_tier(ts.len(), segments, "IVA-Occurrences", "int")
            trs_out.append(tier)

        if self._options['total'] is True:
            tier = sppasIVA.iva_to_tier(ts.total(), segments, "IVA-Total")
            trs_out.append(tier)

        if self._options['mean'] is True:
            tier = sppasIVA.iva_to_tier(ts.mean(), segments, "IVA-Mean")
            trs_out.append(tier)

        if self._options['median'] is True:
            tier = sppasIVA.iva_to_tier(ts.median(), segments, "IVA-Median")
            trs_out.append(tier)

        if self._options['stdev'] is True:
            tier = sppasIVA.iva_to_tier(ts.stdev(), segments, "IVA-StdDev")
            trs_out.append(tier)

        if self._options['linreg'] is True:
            tier = sppasIVA.iva_to_tier_reglin(ts.intercept_slope(), segments, True)
            trs_out.append(tier)

            tier = sppasIVA.iva_to_tier_reglin(ts.intercept_slope(), segments, False)
            trs_out.append(tier)

        return trs_out

    # -----------------------------------------------------------------------

    def get_input_tiers(self, input_files):
        """Return tiers with values and segments.

        :param input_files: (list)

        """
        # Get the tiers with values and segments
        tier_values_input = None
        tier_segments_input = None

        for filename in input_files:
            parser = sppasTrsRW(filename)
            trs_input = parser.read()
            if tier_values_input is None:
                tier_values_input = trs_input.find(self._options['values'])
            if tier_segments_input is None:
                tier_segments_input = trs_input.find(self._options['segments'])

        # Check input tiers
        if tier_values_input is None:
            logging.error("Tier with values not found: {:s}".format(self._options['values']))
            raise NoTierInputError
        if tier_segments_input is None:
            logging.error("Tier with segments not found: {:s}".format(self._options['segments']))
            raise NoTierInputError
        if tier_segments_input.is_interval() is False:
            raise BadInputError
        if any((tier_values_input.is_float(), tier_values_input.is_int())) is False:
            raise BadInputError
        
        return tier_values_input, tier_segments_input

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        :param input_file: (list of str) Values and/or Segments in a single file or in different ones
        :param opt_input_file: (list of str) Values and/or Segments in a single file or in different ones
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get the input tiers 
        if opt_input_file is not None:
            input_file.extend(opt_input_file)
        tier_values, tier_segments = self.get_input_tiers(input_file)
        
        # Estimate IVA on the tiers
        trs_output = self.convert(tier_values, tier_segments)
        trs_output.set_meta('iva_result_of', input_file[0])

        # Save result in a file
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
        return self._options.get("outputpattern", "-iva")

    def get_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputpattern", "")

    def get_input_opt_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputoptpattern", "")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        An annotated file with measure values (pitch, intensity...)

        """
        # all extension of measure files (neither annotation nor table)
        annot_ext = sppasTrsRW.measure_extensions()
        # all extensions with a reader
        all_ext_in = sppasTrsRW.extensions_in()
        # return a AND of both previous lists, add the dot to each extension
        return ["." + e for e in annot_ext if e in all_ext_in]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_opt_input_extensions():
        """Extensions that the annotation expects for its input filename.

        An annotated file with a sppasTier of type 'interval'.

        """
        # all extension of measure files (neither annotation nor table)
        annot_ext = sppasTrsRW.annot_extensions()
        # all extensions with a reader
        all_ext_in = sppasTrsRW.extensions_in()
        # return a AND of both previous lists, add the dot to each extension
        return ["." + e for e in annot_ext if e in all_ext_in]
