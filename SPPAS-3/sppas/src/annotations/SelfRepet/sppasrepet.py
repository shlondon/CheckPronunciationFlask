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

    src.annotations.SelfRepet.sppasrepet.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging

from sppas.src.config import symbols
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from sppas.src.anndata.aio.aioutils import serialize_labels

from ..searchtier import sppasFindTier
from ..annotationsexc import EmptyOutputError

from .sppasbaserepet import sppasBaseRepet
from .detectrepet import SelfRepetition
from .datastructs import DataSpeaker

# ---------------------------------------------------------------------------

SIL_ORTHO = list(symbols.ortho.keys())[list(symbols.ortho.values()).index("silence")]

# ---------------------------------------------------------------------------


class sppasSelfRepet(sppasBaseRepet):
    """SPPAS Automatic Self-Repetition Detection.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2019  Brigitte Bigi

    Detect self-repetitions. The result has never been validated by an expert.
    This annotation is performed on the basis of time-aligned tokens or lemmas.
    The output is made of 2 tiers with sources and echos.

    """

    def __init__(self, log=None):
        """Create a new sppasRepetition instance.

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasSelfRepet, self).__init__("selfrepet.json", log)

    # -----------------------------------------------------------------------
    # Automatic Detection search
    # -----------------------------------------------------------------------

    @staticmethod
    def __find_next_break(tier, start, span):
        """Return the index of the next interval representing a break.

        It depends on the 'span' value.

        :param tier: (sppasTier)
        :param start: (int) the position of the token where the search will start
        :param span: (int)
        :returns: (int) index of the next interval corresponding to the span

        """
        nb_breaks = 0
        for i in range(start, len(tier)):
            if serialize_labels(tier[i].get_labels()) == SIL_ORTHO:
                nb_breaks += 1
                if nb_breaks == span:
                    return i
        return len(tier) - 1

    # -----------------------------------------------------------------------

    def __fix_indexes(self, tier, tok_start, shift):
        tok_start += shift
        tok_search = sppasSelfRepet.__find_next_break(
            tier, tok_start + 1, span=1)
        tok_end = sppasSelfRepet.__find_next_break(
            tier, tok_start + 1, span=self._options['span'])

        return tok_start, tok_search, tok_end

    # -----------------------------------------------------------------------

    def self_detection(self, tier):
        """Self-Repetition detection.

        :param tier: (sppasTier)

        """
        # Create output data
        trs_output = sppasTranscription(self.name)
        trs_output.create_tier("SR-Source")
        trs_output.create_tier("SR-SrcStrain")
        trs_output.create_tier("SR-SrcLen")
        trs_output.create_tier("SR-SrcType")
        trs_output.create_tier("SR-Repet")

        # Use the appropriate stop-list
        stop_words = self._stop_words.copy()
        stop_words.evaluate(tier, merge=True)
        # Create a data structure to detect and store a source/echos
        repetition = SelfRepetition(stop_words)

        # Initialization of the indexes to work with tokens
        tok_start, tok_search, tok_end = self.__fix_indexes(tier, 0, 0)

        # Detection is here:
        while tok_start < tok_end:

            # Build an array with the tokens
            tokens = [serialize_labels(tier[i].get_labels())
                      for i in range(tok_start, tok_end+1)]
            speaker = DataSpeaker(tokens)

            # Detect the first self-repetition in these data
            limit = tok_search - tok_start
            repetition.detect(speaker, limit)

            # Save the repetition (if any)
            shift = 1
            if repetition.get_source() is not None:
                sppasSelfRepet.__add_repetition(repetition, tier, tok_start, trs_output)
                (src_start, src_end) = repetition.get_source()
                shift = src_end + 1

            # Fix indexes for the next search
            tok_start, tok_search, tok_end = self.__fix_indexes(
                tier, tok_start, shift)

        return trs_output

    # -----------------------------------------------------------------------

    @staticmethod
    def __add_repetition(repetition, spk_tier, start_idx, trs_out):
        """Add a repetition - source and echos - in tiers.

        :param repetition: (DataRepetition)
        :param spk_tier: (sppasTier) The tier of the speaker (to detect sources)
        :param start_idx: (int) start index of the interval in spk_tier
        :param src_tier: (sppasTier) The resulting tier with sources
        :param echo_tier: (sppasTier) The resulting tier with echos
        :returns: (bool) the repetition was added or not

        """
        src_tier = trs_out.find("SR-Source")
        echo_tier = trs_out.find("SR-Repet")
        sr_index = len(src_tier)

        # Source
        s, e = repetition.get_source()
        src_begin = spk_tier[start_idx + s].get_lowest_localization()
        src_end = spk_tier[start_idx + e].get_highest_localization()
        iitime = sppasInterval(src_begin.copy(), src_end.copy())
        try:
            a = src_tier.create_annotation(
                    sppasLocation(iitime),
                    sppasLabel(sppasTag("S" + str(sr_index + 1))))
            src_id = a.get_meta('id')
        except:
            return False

        # Echos
        echo_labels = list()
        for (s, e) in repetition.get_echos():
            rep_begin = spk_tier[start_idx + s].get_lowest_localization()
            rep_end = spk_tier[start_idx + e].get_highest_localization()
            eetime = sppasInterval(rep_begin.copy(), rep_end.copy())
            anns = spk_tier.find(rep_begin, rep_end)
            for a in anns:
                for lbl in a.get_labels():
                    echo_labels.append(lbl.copy())
            a = echo_tier.create_annotation(sppasLocation(eetime), sppasLabel(sppasTag("R" + str(sr_index + 1))))
            a.set_meta('is_self_repetition_of', src_id)

        # Source complements: lemmas, len, type
        anns = spk_tier.find(src_begin, src_end)
        src_labels = list()
        for a in anns:
            for lbl in a.get_labels():
                src_labels.append(lbl.copy())
        a = trs_out.find("SR-SrcStrain").create_annotation(sppasLocation(iitime), src_labels)
        a.set_meta('source_id', src_id)
        a = trs_out.find("SR-SrcLen").create_annotation(sppasLocation(iitime), sppasLabel(sppasTag(len(src_labels), "int")))
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
        a = trs_out.find("SR-SrcType").create_annotation(sppasLocation(iitime), sppasLabel(sppasTag(or_type)))
        a.set_meta('source_id', src_id)
        logging.info("OR {:d}. {} {} -> {:s}".format(sr_index+1, src_labels, echo_labels, or_type))

        return True

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        :param input_file: (list of str) time-aligned tokens
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get the tier to be used
        parser = sppasTrsRW(input_file[0])
        trs_input = parser.read()
        tier_tokens = sppasFindTier.aligned_tokens(trs_input)
        tier_input = self.make_word_strain(tier_tokens)

        # Repetition Automatic Detection
        trs_output = self.self_detection(tier_input)

        # Create the transcription result
        trs_output.set_meta('self_repetition_result_of', input_file[0])
        self.transfer_metadata(trs_input, trs_output)

        if len(self._word_strain) > 0:
            trs_output.append(tier_input)
        if self._options['stopwords'] is True:
            trs_output.append(self.make_stop_words(tier_input))

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
        return self._options.get("outputpattern", "-srepet")

    def get_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputpattern", "-palign")
