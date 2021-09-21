"""
:filename: sppas.src.annotations.Overlaps.sppasoverlaps.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the overlaps automatic annotation

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

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import EmptyOutputError
from ..annotationsexc import NoTierInputError
from ..baseannot import sppasBaseAnnotation

from .overspeech import OverActivity

# ----------------------------------------------------------------------------


class sppasOverActivity(sppasBaseAnnotation):
    """SPPAS integration of the automatic overlaps estimator on intervals.

    """

    def __init__(self, log=None):
        """Create a new instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasOverActivity, self).__init__("overlaps.json", log)
        self.__out_items = list()
        self.set_default_out_items()

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if "tiername" == key:
                self.set_tiername(opt.get_value())

            elif "ignore" == key:
                self.set_out_items(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def set_tiername(self, tier_name):
        """Fix the tiername option.

        :param tier_name: (str)

        """
        self._options['tiername'] = sppasUnicode(tier_name).to_strip()

    # -----------------------------------------------------------------------

    def set_out_items(self, str_entry):
        """Fix the list of tags to be ignored from the given string.

        :param str_entry: (str) Entries separated by commas

        """
        self.__out_items = list()
        items = str_entry.split(",")
        if len(items) > 0:
            for item in items:
                item = item.strip()
                if len(item) > 0:
                    self.__out_items.append(item)

    # ----------------------------------------------------------------------

    def set_default_out_items(self):
        """Set the list of tags to be ignored."""
        self.__out_items = list()
        self.__out_items.append("dummy")
        self.__out_items.append("noise")
        self.__out_items.append("pause")

    # ----------------------------------------------------------------------
    # The search for overlaps is here
    # ----------------------------------------------------------------------

    def detection(self, tier_spk1, tier_spk2):
        """Search for the overlaps of annotations.

        :param tier_spk1: (sppasTier)
        :param tier_spk2: (sppasTier)

        """
        out_tags = list()
        # Convert out items into out tags
        if tier_spk1.is_bool() and tier_spk2.is_bool():
            for item in self.__out_items:
                tag = sppasTag(item, tag_type="bool")
                out_tags.append(tag)
        elif tier_spk1.is_float() and tier_spk2.is_float():
            for item in self.__out_items:
                tag = sppasTag(item, tag_type="float")
                out_tags.append(tag)
        elif tier_spk1.is_int() and tier_spk2.is_int():
            for item in self.__out_items:
                tag = sppasTag(item, tag_type="int")
                out_tags.append(tag)
        elif tier_spk1.is_string() and tier_spk2.is_string():
            for item in self.__out_items:
                tag = sppasTag(item, tag_type="str")
                out_tags.append(tag)
        else:
            raise Exception("Two non-empty tiers of the same type were expected.")

        over = OverActivity(out_tags)
        return over.overlaps(tier_spk1, tier_spk2)

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return 2 tiers with name given in options.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (sppasTier)

        """
        if len(input_files) != 2:
            raise Exception("Invalid format of input files.")

        tier_src = None
        for filename in input_files[0]:
            parser = sppasTrsRW(filename)
            trs_input = parser.read()
            if tier_src is None:
                tier_src = trs_input.find(self._options['tiername'], case_sensitive=False)
        if tier_src is None:
            logging.error("A tier with name {:s} was expected but not found."
                          "".format(self._options['tiername']))
            raise NoTierInputError

        tier_echo = None
        for filename in input_files[1]:
            parser = sppasTrsRW(filename)
            trs_input = parser.read()
            if tier_echo is None:
                tier_echo = trs_input.find(self._options['tiername'], case_sensitive=False)
        if tier_echo is None:
            logging.error("A tier with name {:s} was expected but not found."
                          "".format(self._options['tiername']))
            raise NoTierInputError

        return tier_src, tier_echo

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        Input files is a list with 2 files:
        the activity of speaker 1 and the activity of the speaker 2.

        :param input_files: (list of str) Time-aligned items, Time-aligned items
        :param output: (str) the output name
        :returns: (sppasTranscription)

        """
        # Get the tier to be used
        tier_spk1, tier_spk2 = self.get_inputs(input_files)

        # Overlaps Automatic Detection
        new_tier = self.detection(tier_spk1, tier_spk2)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0][0])
        trs_output.append(new_tier)

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

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-overlaps")

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [self._options.get("inputpattern", "-activity")]
