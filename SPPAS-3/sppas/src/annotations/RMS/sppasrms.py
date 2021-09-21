# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.RMS.sppasrms.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of RMS automatic annotation

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
import os

from sppas.src.utils import sppasUnicode
import sppas.src.audiodata.aio
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTag
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasMedia
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata.anndataexc import AnnDataTypeError

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoChannelInputError
from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyInputError
from ..annotationsexc import EmptyOutputError
from ..baseannot import sppasBaseAnnotation
from ..autils import SppasFiles

from .irms import IntervalsRMS

# ----------------------------------------------------------------------------


class sppasRMS(sppasBaseAnnotation):
    """SPPAS integration of the automatic RMS estimator on intervals.

    Estimate the root-mean-square of segments, i.e. sqrt(sum(S_i^2)/n).
    This is a measure of the power in an audio signal.

    """

    def __init__(self, log=None):
        """Create a new sppasRMS instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasRMS, self).__init__("rms.json", log)
        self.__rms = IntervalsRMS()

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

    # ----------------------------------------------------------------------
    # The RMS estimator is here
    # ----------------------------------------------------------------------

    def estimator(self, tier):
        """Estimate RMS on all non-empty intervals.

        :param tier: (sppasTier)

        """
        rms_avg = sppasTier("RMS")
        rms_values = sppasTier("RMS-values")
        rms_mean = sppasTier("RMS-mean")

        for ann in tier:

            content = serialize_labels(ann.get_labels())
            if len(content) == 0:
                continue

            # Localization of the current annotation
            begin = ann.get_lowest_localization()
            end = ann.get_highest_localization()

            # Estimate all RMS values during this ann
            self.__rms.estimate(begin.get_midpoint(), end.get_midpoint())

            # The global RMS of the fragment between begin and end
            rms_tag = sppasTag(self.__rms.get_rms(), "int")
            rms_avg.create_annotation(
                ann.get_location().copy(),
                sppasLabel(rms_tag)
            )

            # All the RMS values (one each 10 ms)
            labels = list()
            for value in self.__rms.get_values():
                labels.append(sppasLabel(sppasTag(value, "int")))
            rms_values.create_annotation(ann.get_location().copy(), labels)

            # The fmean RMS of the fragment between begin and end
            rms_mean_tag = sppasTag(self.__rms.get_fmean(), "float")
            rms_mean.create_annotation(
                ann.get_location().copy(),
                sppasLabel(rms_mean_tag)
            )

        return rms_avg, rms_values, rms_mean

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the channel and the tier with ipus.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (sppasChannel, sppasTier)

        """
        # Get the tier and the channel
        ext = self.get_input_extensions()
        audio_ext = ext[0]
        annot_ext = ext[1]
        tier = None
        channel = None
        audio_filename = ""

        for filename in input_files:
            fn, fe = os.path.splitext(filename)

            if channel is None and fe in audio_ext:
                audio_speech = sppas.src.audiodata.aio.open(filename)
                n = audio_speech.get_nchannels()
                if n != 1:
                    audio_speech.close()
                idx = audio_speech.extract_channel()
                channel = audio_speech.get_channel(idx)
                audio_filename = filename
                audio_speech.close()

            elif tier is None and fe in annot_ext:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = trs_input.find(self._options['tiername'], case_sensitive=False)

        # Check input tier
        if tier is None:
            logging.error("Tier with name '{:s}' not found."
                          "".format(self._options['tiername']))
            raise NoTierInputError
        if tier.is_interval() is False:
            logging.error("The tier should be of type: Interval.")
            raise AnnDataTypeError(tier.get_name(), 'IntervalTier')
        if tier.is_empty() is True:
            raise EmptyInputError(self._options['tiername'])

        # Check input channel
        if channel is None:
            logging.error("No audio file found or invalid one. "
                          "An audio file with only one channel was expected.")
            raise NoChannelInputError

        # Set the media to the input tier
        extm = os.path.splitext(audio_filename)[1].lower()[1:]
        media = sppasMedia(os.path.abspath(audio_filename), mime_type="audio/"+extm)
        tier.set_media(media)

        return channel, tier

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        Input file is a tuple with 2 files:
        the audio file and the annotation file

        :param input_files: (list of str) (audio, time-aligned items)
        :param output: (str) the output name
        :returns: (sppasTranscription)

        """
        channel, tier = self.get_inputs(input_files)
        self.__rms.set_channel(channel)

        # RMS Automatic Estimator
        new_tiers = self.estimator(tier)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        for t in new_tiers:
            trs_output.append(t)

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
        return self._options.get("outputpattern", "-rms")

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", ""),
            self._options.get("inputpattern2", "-palign")
        ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename."""
        return [
            SppasFiles.get_informat_extensions("AUDIO"),
            SppasFiles.get_informat_extensions("ANNOT_ANNOT")
        ]
