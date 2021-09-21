# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.StopWords.sppaswtpwds.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the StopWords automatic annotation.

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
import os

from sppas.src.config import symbols
from sppas.src.utils import sppasUnicode

from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag

from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyOutputError
from ..baseannot import sppasBaseAnnotation
from ..annotationsexc import AnnotationOptionError
from .stpwds import StopWords

# ----------------------------------------------------------------------------


class sppasStopWords(sppasBaseAnnotation):
    """SPPAS integration of the identification of stop words in a tier.

    """

    def __init__(self, log=None):
        """Create a new instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasStopWords, self).__init__("stopwords.json", log)
        self._stops = StopWords()

    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: list of sppasOption instances

        """
        for opt in options:

            key = opt.get_key()

            if "alpha" == key:
                self.set_alpha(opt.get_value())

            elif "tiername" == key:
                self.set_tiername(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_alpha(self, alpha):
        """Fix the alpha option.

        Alpha is a coefficient to add specific stop-words in the list.

        :param alpha: (float)

        """
        self._stops.set_alpha(alpha)
        self._options['alpha'] = alpha

    # -----------------------------------------------------------------------

    def set_tiername(self, tier_name):
        """Fix the tiername option.

        :param tier_name: (str)

        """
        self._options['tiername'] = sppasUnicode(tier_name).to_strip()

    # -----------------------------------------------------------------------

    def load_resources(self, lang_resources, lang=None):
        """Load a list of stop-words and replacements.

        Override the existing loaded lists...

        :param lang_resources: (str) File with extension '.stp' or nothing
        :param lang: (str)

        """
        fn, fe = os.path.splitext(lang_resources)

        try:
            stp = fn + '.stp'
            self._stops.load(stp, merge=False)
            self.logfile.print_message(
                "The initial list contains {:d} stop-words"
                "".format(len(self._stops)), indent=0)

        except Exception as e:
            self._stops.clear()
            self.logfile.print_message(
                "No stop-words loaded: {:s}".format(str(e)), indent=1)

    # -----------------------------------------------------------------------

    def make_stp_tier(self, tier):
        """Return a tier indicating if entries are stop-words.

        :param tier: (sppasTier)

        """
        # Evaluate the new list of stop words
        stops = self._stops.copy()
        nb = stops.evaluate(tier, merge=True)
        self.logfile.print_message(
            "Number of stop-words evaluated: {:d}".format(nb),
            indent=1)
        self.logfile.print_message(
            "The list contains {:d} stop-words"
            "".format(len(stops)), indent=1)
        logging.info("Vocabulary size: {:d}".format(stops.get_v()))
        logging.info("Threshold proba: {:f}".format(stops.get_threshold()))

        stp_tier = sppasTier('IsStopWord')
        for ann in tier:
            new_labels = list()
            for label in ann.get_labels():
                tag = label.get_best()
                content = tag.get_content()
                if content not in symbols.all:
                    stp = stops.is_in(content)
                    new_labels.append(sppasLabel(sppasTag(stp, tag_type="bool")))

            stp_tier.create_annotation(ann.get_location().copy(), new_labels)

        return stp_tier

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the the tier with aligned tokens.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (sppasTier)

        """
        tier = None
        annot_ext = self.get_input_extensions()

        for filename in input_files:
            fn, fe = os.path.splitext(filename)
            if tier is None and fe in annot_ext[0]:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = trs_input.find(self._options['tiername'], case_sensitive=False)
                if tier is not None:
                    return tier

        # Check input tier
        logging.error("A tier with name {:s} was not found."
                      "".format(self._options['tiername']))
        raise NoTierInputError

    # ----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) Time-aligned tokens
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get the tier to be used
        tier = self.get_inputs(input_files)

        # Detection
        stp_tier = self.make_stp_tier(tier)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        trs_output.append(stp_tier)

        # Save in a file
        if output is not None:
            output_file = self.fix_out_file_ext(output)
            if len(trs_output) > 0:
                parser = sppasTrsRW(output_file)
                parser.write(trs_output)
                return [output_file]
            else:
                raise EmptyOutputError

        return trs_output

    # ----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-stops")
