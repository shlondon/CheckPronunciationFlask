# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.OtherRepet.sppasrepet.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the detection of other-repetitions.

.. _This file is part of SPPAS: <http://www.sppas.org/>
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

from sppas.src.config import symbols
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag

from sppas.src.anndata.anndataexc import TierAddError
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata.aio.aioutils import fill_gaps

from ..annotationsexc import AnnotationOptionError
from ..searchtier import sppasFindTier
from ..annotationsexc import EmptyOutputError
from ..SelfRepet.datastructs import DataSpeaker
from ..SelfRepet.sppasbaserepet import sppasBaseRepet

from .detectrepet import OtherRepetition

# ---------------------------------------------------------------------------

SIL_ORTHO = list(symbols.ortho.keys())[list(symbols.ortho.values()).index("silence")]

# ---------------------------------------------------------------------------


class sppasOtherRepet(sppasBaseRepet):
    """SPPAS Automatic Other-Repetition Detection.

    Detect automatically other-repetitions. Result must be re-filtered by an
    expert. This annotation is performed on the basis of time-aligned tokens
    or lemmas. The output is made of 2 tiers with sources and echos.

    """

    def __init__(self, log=None):
        """Create a new sppasOtherRepet instance.

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasOtherRepet, self).__init__("otherrepet.json", log)

        self.max_span = 12

    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: list of sppasOption instances

        """
        for opt in options:

            key = opt.get_key()

            if "stopwords" == key:
                self.set_use_stopwords(opt.get_value())

            elif "span" == key:
                self.set_span(opt.get_value())

            elif "alpha" == key:
                self.set_alpha(opt.get_value())

            elif "allechos" == key:
                self.set_all_echos_tier(opt.get_value())

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_all_echos_tier(self, all_echos):
        """Create a tier with all tokens that are echo-candidates.

        :param all_echos: (bool)

        """
        self._options['allechos'] = bool(all_echos)

    # -----------------------------------------------------------------------
    # Automatic Detection search
    # -----------------------------------------------------------------------

    def other_detection(self, inputtier1, inputtier2):
        """Other-Repetition detection.

        :param inputtier1: (Tier)
        :param inputtier2: (Tier)

        """
        if inputtier1.is_float():
            inputtier1.set_radius(0.04)
        if inputtier2.is_float():
            inputtier2.set_radius(0.04)
        # Use the appropriate stop-list: add un-relevant tokens of the echoing speaker
        stop_words = self._stop_words.copy()
        stop_words.evaluate(inputtier2, merge=True)
        # Create repeat objects
        repetition = OtherRepetition(stop_words)
        # Create output data
        trs_output = sppasTranscription(self.name)
        trs_output.create_tier("OR-Source")
        trs_output.create_tier("OR-SrcStrain")
        trs_output.create_tier("OR-SrcLen")
        trs_output.create_tier("OR-SrcType")
        trs_output.create_tier("OR-Echo")
        if self._options['allechos'] is True:
            trs_output.create_tier("OR-AllEchos")

        # Initialization of tok_start, and tok_end
        tok_start_src = 0
        tok_end_src = min(20, len(inputtier1)-1)  # 20 is the max nb of tokens in a src
        tok_start_echo = 0

        tokens2 = list()
        speaker2 = DataSpeaker(tokens2)
        # Detection is here:
        # detect() is applied word by word, from tok_start to tok_end
        while tok_start_src < tok_end_src:

            # Build an array with the tokens
            tokens1 = [serialize_labels(inputtier1[i].get_labels())
                       for i in range(tok_start_src, tok_end_src+1)]
            speaker1 = DataSpeaker(tokens1)

            # Create speaker2
            # re-create only if different of the previous step...
            src_begin = inputtier1[tok_start_src].get_lowest_localization().get_midpoint()
            echo_begin = inputtier2[tok_start_echo].get_lowest_localization().get_midpoint()
            if len(tokens2) == 0 or echo_begin < src_begin:
                tokens2 = list()
                nb_breaks = 0
                init_tok_start_echo = tok_start_echo
                tok_start_echo = -1

                for i in range(init_tok_start_echo, len(inputtier2)):
                    ann = inputtier2[i]
                    # append tokens only if ann is during or after the beginning of the source
                    if ann.get_lowest_localization().get_midpoint() >= src_begin:
                        label = serialize_labels(ann.get_labels())
                        if tok_start_echo == -1:
                            tok_start_echo = i
                        if label == SIL_ORTHO:
                            nb_breaks += 1
                        if nb_breaks == self._options['span']:
                            break
                        tokens2.append(label)
                speaker2 = DataSpeaker(tokens2)

            # We can't go too further due to the required time-alignment of
            # tokens between src/echo
            # Check only if the first token is the first token of a source!!
            repetition.detect(speaker1, speaker2, 1)

            # Save repeats
            shift = 1
            if repetition.get_source() is not None:
                s, e = repetition.get_source()
                saved = sppasOtherRepet.__add_repetition(repetition, inputtier1, inputtier2, tok_start_src, tok_start_echo, trs_output)
                if saved is True:
                    shift = e + 1

            tok_start_src = min(tok_start_src + shift, len(inputtier1)-1)
            tok_end_src = min(tok_start_src + 20, len(inputtier1)-1)

        return trs_output

    # -----------------------------------------------------------------------

    @staticmethod
    def __add_repetition(repetition, spk1_tier, spk2_tier, start_idx1, start_idx2, trs_out):
        """Add a repetition - source and echos - in tiers.

        :param repetition: (DataRepetition)
        :param spk1_tier: (Tier) The tier of speaker 1 (to detect sources)
        :param spk2_tier: (Tier) The tier of speaker 2 (to detect echos)
        :param start_idx1: start index of the interval in spk1_tier
        :param start_idx2: start index of the interval in spk2_tier
        :param trs_out: (sppasTranscription) The resulting tiers
        :returns: (bool) the repetition was added or not

        """
        src_tier = trs_out.find("OR-Source")
        echo_tier = trs_out.find("OR-Echo")
        or_index = len(src_tier)

        # Source
        s, e = repetition.get_source()
        src_begin = spk1_tier[start_idx1 + s].get_lowest_localization()
        src_end = spk1_tier[start_idx1 + e].get_highest_localization()
        iitime = sppasInterval(src_begin.copy(), src_end.copy())
        try:
            a = src_tier.create_annotation(sppasLocation(iitime), sppasLabel(sppasTag("S" + str(or_index + 1))))
            src_id = a.get_meta('id')
        except TierAddError:
            return False
        logging.debug("==> Source {:d}".format(or_index))

        # Echos
        echo_labels = list()
        for (s, e) in repetition.get_echos():
            rep_begin = spk2_tier[start_idx2 + s].get_lowest_localization()
            rep_end = spk2_tier[start_idx2 + e].get_highest_localization()
            anns = spk2_tier.find(rep_begin, rep_end)
            for a in anns:
                for lbl in a.get_labels():
                    echo_labels.append(lbl.copy())
                    logging.debug("    -> echo {} {}: {}".format(s, e, lbl))
            eetime = sppasInterval(rep_begin.copy(), rep_end.copy())
            r = sppasLabel(sppasTag("R" + str(or_index + 1)))
            try:
                a = echo_tier.create_annotation(sppasLocation(eetime), r)
                a.set_meta('source_id', src_id)
            except TierAddError:
                a = echo_tier.find(rep_begin, rep_end)
                if len(a) > 0:
                    a[0].append_label(r)

        # Source complements: lemmas, len, type
        anns = spk1_tier.find(src_begin, src_end)
        src_labels = list()
        for a in anns:
            for lbl in a.get_labels():
                src_labels.append(lbl.copy())
                logging.debug("    => src: {}".format(lbl))
        a = trs_out.find("OR-SrcStrain").create_annotation(sppasLocation(iitime), src_labels)
        a.set_meta('source_id', src_id)
        a = trs_out.find("OR-SrcLen").create_annotation(sppasLocation(iitime), sppasLabel(sppasTag(len(src_labels), "int")))
        a.set_meta('source_id', src_id)
        # type is either: strict, split, reduction, variation
        or_type = "variation"
        if len(repetition.get_echos()) > 1:
            or_type = "split:{:d}".format(len(repetition.get_echos()))
        elif len(src_labels) > len(echo_labels):
            or_type = "reduction"
        else:
            if len(src_labels) == len(echo_labels):
                equals = True
                for ls, le in zip(src_labels, echo_labels):
                    if ls.get_best() != le.get_best():
                        equals = False
                        break
                if equals is True:
                    or_type = "strict"
        a = trs_out.find("OR-SrcType").create_annotation(sppasLocation(iitime), sppasLabel(sppasTag(or_type)))
        a.set_meta('source_id', src_id)

        # Echo complement: all echo tokens
        all_echos_tier = trs_out.find("OR-AllEchos")
        if all_echos_tier is not None:
            for tok_idx in repetition.get_all_echos():
                ann = spk2_tier[start_idx2 + tok_idx]
                r = sppasLabel(sppasTag("R" + str(or_index + 1)))
                find_a = all_echos_tier.find(ann.get_lowest_localization(), ann.get_highest_localization(), overlaps=False)
                if len(find_a) == 1:
                    find_a[0].append_label(r)
                else:
                    a = ann.copy()
                    a.set_labels([r])
                    all_echos_tier.add(a)

                a.set_meta('source_id_of_R{:d}'.format(or_index + 1), src_id)
        return True

    # -----------------------------------------------------------------------
    # Run
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        Input file is a tuple with 2 files: the main speaker and the echoing
        speaker.

        :param input_file: (list of str) (time-aligned token, time-aligned token)
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output name
        :returns: (sppasTranscription)

        """
        # Get the tier to be used -- source
        parser = sppasTrsRW(input_file[0])
        trs_input1 = parser.read()
        tier_tokens = sppasFindTier.aligned_tokens(trs_input1)
        # Check if silences are indicated
        s = 0
        for ann in tier_tokens:
            if ann.is_labelled():
                if ann.get_best_tag().is_silence() is True:
                    s += 1
        if (float(s) / float(len(tier_tokens))) < 0.05:
            logging.error("Error. The tier with tokens should contain silences but it doesn't."
                          "To detect the repetitions, the Inter Pausal Units are required to"
                          "fix the span. Without silences, there's no way to know where the"
                          "IPUs are...")
            raise ValueError("Invalid input tier {:s}: no silences.".format(tier_tokens.get_name()))
        tier_input1 = self.make_word_strain(tier_tokens)
        tier_input1.set_name(tier_input1.get_name() + "-source")

        # Get the tier to be used -- echo
        parser = sppasTrsRW(input_file[1])
        trs_input2 = parser.read()
        tier_tokens = sppasFindTier.aligned_tokens(trs_input2)
        s = 0
        min_time_point = trs_input2.get_min_loc()
        max_time_point = trs_input2.get_max_loc()
        tier_tokens = fill_gaps(tier_tokens, min_time_point, max_time_point)
        for ann in tier_tokens:
            if ann.is_labelled():
                if ann.get_best_tag().is_silence() is True:
                    s += 1
                content = ann.get_best_tag().get_content()
                if len(content) == 0:
                    ann.set_labels([sppasLabel(sppasTag('#'))])
            else:
                ann.set_labels([sppasLabel(sppasTag('#'))])
        if (float(s) / float(len(tier_tokens))) < 0.05:
            logging.error("Error. The tier with tokens should contain silences but it doesn't. "
                          "To detect the repetitions, the Inter Pausal Units are required to "
                          "fix the span. Without silences, there's no way to know where the "
                          "IPUs are...")
            raise ValueError("Invalid input tier {:s}: no silences.".format(tier_tokens.get_name()))
        tier_input2 = self.make_word_strain(tier_tokens)
        tier_input2.set_name(tier_input2.get_name() + "-echo")

        # Repetition Automatic Detection
        trs_output = self.other_detection(tier_input1, tier_input2)
        self.transfer_metadata(trs_input1, trs_output)
        trs_output.set_meta('other_repetition_result_of_source', input_file[0])
        trs_output.set_meta('other_repetition_result_of_echo', input_file[1])
        if len(self._word_strain) > 0:
            trs_output.append(tier_input1)
        if self._options['stopwords'] is True:
            trs_output.append(self.make_stop_words(tier_input1))
        if len(self._word_strain) > 0:
            trs_output.append(tier_input2)

        # Save in a file
        if output is not None:
            if len(trs_output) > 0:
                output_file = self.fix_out_file_ext(output)
                parser = sppasTrsRW(output_file)
                parser.write(trs_output)
                # self.print_filename(output_file)
                return [output_file]
            else:
                raise EmptyOutputError

        return trs_output

    # ----------------------------------------------------------------------

    def get_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-orepet")

    def get_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputpattern", "-palign")
