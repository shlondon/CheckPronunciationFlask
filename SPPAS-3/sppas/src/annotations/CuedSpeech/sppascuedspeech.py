# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.CuedSpeech.sppascuedspeech.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the Cued Speech automatic annotation.

.. _This file is part of SPPAS: <http://www.sppas.org/>
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

"""

import os

from sppas.src.config import cfg
from sppas.src.config import symbols
from sppas.src.config import annots
from sppas.src.config import info

from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasMedia

from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import EmptyOutputError

from .lpckeys import CuedSpeechKeys
from .lpcvideo import CuedSpeechVideoTagger

# ---------------------------------------------------------------------------


class sppasCuedSpeech(sppasBaseAnnotation):
    """SPPAS integration of the automatic Cued Speech key-code generation.

    """

    def __init__(self, log=None):
        """Create a new instance.

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasCuedSpeech, self).__init__("lpc.json", log)
        self.__lpc = CuedSpeechKeys()
        self.__tagger = CuedSpeechVideoTagger()

    # -----------------------------------------------------------------------

    def load_resources(self, config_filename, image_filename, **kwargs):
        """Fix the keys from a configuration file.

        :param config_filename: Name of the configuration file with the keys

        """
        self.__lpc = CuedSpeechKeys(config_filename)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        Available options are:

            - createvideo

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if "createvideo" == key:
                self.set_create_video(opt.get_value())

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_create_video(self, create=True):
        """Fix the createvideo option.

        :param create: (bool)

        """
        self._options['createvideo'] = create

    # -----------------------------------------------------------------------
    # Syllabification of time-aligned phonemes stored into a tier
    # -----------------------------------------------------------------------

    def convert(self, phonemes):
        """Syllabify labels of a time-aligned phones tier.

        :param phonemes: (sppasTier) time-aligned phonemes tier
        :returns: (sppasTier)

        """
        lpc_tier = sppasTier("CuedSpeechSyll")
        lpc_tier.set_meta('cued_speech_syll_of_tier', phonemes.get_name())

        # create a tier without the separators, i.e. keep only the phonemes
        intervals = sppasCuedSpeech._phon_to_intervals(phonemes)

        # generate keys for each sequence of phonemes
        for interval in intervals:

            # get the index of the phonemes containing the begin
            # of the interval
            start_phon_idx = phonemes.lindex(interval.get_lowest_localization())
            if start_phon_idx == -1:
                start_phon_idx = phonemes.mindex(interval.get_lowest_localization(), bound=-1)

            # get the index of the phonemes containing the end of the interval
            end_phon_idx = phonemes.rindex(interval.get_highest_localization())
            if end_phon_idx == -1:
                end_phon_idx = phonemes.mindex(interval.get_highest_localization(), bound=1)

            # generate keys within the interval
            if start_phon_idx != -1 and end_phon_idx != -1:
                self.gen_keys_interval(phonemes, start_phon_idx, end_phon_idx, lpc_tier)
            else:
                self.logfile.print_message(
                    (info(1224, "annotations")).format(interval),
                    indent=2, status=annots.warning)

        return lpc_tier

    # -----------------------------------------------------------------------

    def gen_keys_interval(self, tier_palign, from_p, to_p, lpc_keys):
        """Perform the key generation of one sequence of phonemes.

        :param tier_palign: (sppasTier)
        :param from_p: (int) index of the first phoneme to be syllabified
        :param to_p: (int) index of the last phoneme to be syllabified
        :param lpc_keys: (sppasTier)

        """
        # create the sequence of phonemes to syllabify and their durations
        phons = list()
        durations = list()
        for ann in tier_palign[from_p:to_p+1]:
            dur = ann.get_location().get_best().duration()
            durations.append(dur.get_value())
            tag = ann.get_best_tag()
            phons.append(tag.get_typed_content())

        # create the sequence of keys
        syll_keys = self.__lpc.syllabify(phons, durations)

        # add the keys into the output tier
        for i, syll in enumerate(syll_keys):
            start_idx, end_idx = syll

            # create the location
            begin = tier_palign[start_idx+from_p].get_lowest_localization().copy()
            end = tier_palign[end_idx+from_p].get_highest_localization().copy()
            location = sppasLocation(sppasInterval(begin, end))

            # create the labels: the consonant and the vowel
            phonetized = self.__lpc.phonetize_syllables(phons, [syll])

            # add the lpc keys into the output tier
            lpc_keys.create_annotation(location, sppasLabel(sppasTag(phonetized)))

    # -----------------------------------------------------------------------

    def create_keys(self, lpc_tier):
        """Return two tiers with the LPC keys from LPC syllables.

        :param lpc_tier: (sppasTier)
        :returns: (sppasTier)

        """
        cv_tier = sppasTier("CuedSpeechCV")
        key_tier = sppasTier("CuedSpeechKey")
        cv_tier.set_meta('cued_speech_cv_key_of_tier', lpc_tier.get_name())
        key_tier.set_meta('cued_speech_key_of_tier', lpc_tier.get_name())
        for ann in lpc_tier:
            key_label = "00"
            key_labels = list()
            if ann.is_labelled() is True:
                tag = ann.get_best_tag()
                phonetized = tag.get_content()
                c, v = self.__lpc.syll_to_key(phonetized)
                key_labels = [sppasLabel(sppasTag(c)), sppasLabel(sppasTag(v))]
                key_label = sppasLabel(sppasTag(c+v))

            a1 = ann.copy()
            a1.set_labels(key_labels)
            cv_tier.add(a1)

            a2 = ann.copy()
            a2.set_labels([key_label])
            key_tier.add(a2)

        return cv_tier, key_tier

    # -----------------------------------------------------------------------

    def make_video(self, video_file, landmarks, lpc_keys, output):
        """Create a video with the LPC keys.

        :param video_file: (str) Filename of the video
        :param landmarks: (str) Filename of the CSV with landmarks
        :param lpc_keys: (sppasTier) Codes of the C-V syllables

        """
        if cfg.feature_installed("video") is True:
            self.logfile.print_message("Create the tagged video", status=annots.info)
            self.__tagger.load(video_file, landmarks)
            self.__tagger.tag(lpc_keys, output)
            self.__tagger.close()
        else:
            self.logfile.print_message(
                "To tag a video, the video support feature must be enabled."
                "", status=annots.error)

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        :param input_file: (list of str) time-aligned phonemes, video file
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output name
        :returns: (sppasTranscription)

        """
        # Get the tier from which we'll generate LPC keys
        parser = sppasTrsRW(input_file[0])
        trs_input = parser.read()
        tier_input = sppasFindTier.aligned_phones(trs_input)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('lpc_result_of', input_file[0])
        self.transfer_metadata(trs_input, trs_output)

        # Create the tier with the lpc syllables
        tier_lpc = self.convert(tier_input)
        trs_output.append(tier_lpc)
        # Create the tier with the lpc keys
        tier_cv_keys, tier_key = self.create_keys(tier_lpc)
        trs_output.append(tier_key)
        trs_output.append(tier_cv_keys)

        # Add sppasMedia into the output tiers
        if len(opt_input_file) > 0:
            extm = os.path.splitext(opt_input_file[0])[1].lower()[1:]
            media = sppasMedia(os.path.abspath(opt_input_file[0]),
                               mime_type="video/" + extm)
            tier_lpc.set_media(media)
            tier_key.set_media(media)
            tier_cv_keys.set_media(media)

        # Extra result: create a video with the keys
        if self._options['createvideo']:
            do_vid = False
            if len(opt_input_file) > 1:
                video = opt_input_file[0]
                sights = opt_input_file[1]
                if video is not None and sights is not None:
                    do_vid = True
                    self.make_video(video, sights, tier_cv_keys, output)
            if do_vid is False:
                self.logfile.print_message(
                    "The option to tag the video was enabled but no video/csv "
                    "was found related to the annotated file {}"
                    "".format(input_file[0]), status=-1)

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
        return self._options.get("outputpattern", "-lpc")

    def get_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("inputpattern", "-palign")

    def get_opt_input_pattern(self):
        """Pattern this annotation expects for its input filename."""
        return self._options.get("optinputpattern", "-sights")

    # -----------------------------------------------------------------------
    # Utilities:
    # -----------------------------------------------------------------------

    @staticmethod
    def _phon_to_intervals(phonemes):
        """Create the intervals to be syllabified.

        We could use symbols.phone only, but for backward compatibility
        we hardly add the symbols we previously used into SPPAS.

        :return: a tier with the consecutive filled intervals.

        """
        stop = list(symbols.phone.keys())
        stop.append('#')
        stop.append('@@')
        stop.append('+')
        stop.append('gb')
        stop.append('lg')

        return phonemes.export_to_intervals(stop)
