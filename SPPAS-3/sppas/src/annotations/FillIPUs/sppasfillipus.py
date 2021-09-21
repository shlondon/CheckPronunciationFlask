# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FillIPUs.sppasfillipus.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Search for IPUS and fill in IPUs with a given transcription.

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

import os
import logging

from sppas.src.config import symbols
from sppas.src.config import info
from sppas.src.config import annots
from sppas.src.utils import u
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasMedia
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
import sppas.src.audiodata.aio
import sppas.src.anndata.aio

from sppas.src.anndata.anndataexc import AnnDataTypeError

from ..annotationsexc import NoTierInputError
from ..annotationsexc import EmptyInputError
from ..annotationsexc import NoChannelInputError
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import AudioChannelError
from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..SearchIPUs.sppassearchipus import sppasSearchIPUs
from ..autils import SppasFiles

from .fillipus import FillIPUs

# ---------------------------------------------------------------------------

SIL_ORTHO = list(symbols.ortho.keys())[list(symbols.ortho.values()).index("silence")]

# ---------------------------------------------------------------------------


def _info(msg_id):
    return u(info(msg_id, "annotations"))

# ---------------------------------------------------------------------------


class sppasFillIPUs(sppasBaseAnnotation):
    """SPPAS integration of the fill in IPUs automatic annotation.

    """

    def __init__(self, log=None):
        """Create a new sppasFillIPUs instance.

        Log is used for a better communication of the annotation process and its
        results. If None, logs are redirected to the default logging system.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasFillIPUs, self).__init__("fillipus.json", log)
        self.__audio_filename = None

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        Available options are:

            - threshold: volume threshold to decide a window is silence or not
            - win_length: length of window for a estimation or volume values
            - min_sil: minimum duration of a silence
            - min_ipu: minimum duration of an ipu
            - shift_start: start boundary shift value.
            - shift_end: end boundary shift value.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if "min_sil" == key:
                self.set_min_sil(opt.get_value())

            elif "min_ipu" == key:
                self.set_min_ipu(opt.get_value())

            elif "shift_start" == key:
                self.set_shift_start(opt.get_value())

            elif "shift_end" == key:
                self.set_shift_end(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def get_min_sil(self):
        return self._options['min_sil']

    def get_min_ipu(self):
        return self._options['min_ipu']

    def get_shift_start(self):
        return self._options['shift_start']

    def get_shift_end(self):
        return self._options['shift_end']

    # -----------------------------------------------------------------------

    def set_min_sil(self, value):
        """Fix the initial minimum duration of a silence.

        :param value: (float) Duration in seconds.

        """
        self._options['min_sil'] = value

    # -----------------------------------------------------------------------

    def set_min_ipu(self, value):
        """Fix the initial minimum duration of an IPU.

        :param value: (float) Duration in seconds.

        """
        self._options['min_ipu'] = value

    # -----------------------------------------------------------------------

    def set_shift_start(self, value):
        """Fix the start boundary shift value.

        :param value: (float) Duration in seconds.

        """
        self._options['shift_start'] = value

    # -----------------------------------------------------------------------

    def set_shift_end(self, value):
        """Fix the end boundary shift value.

        :param value: (float) Duration in seconds.

        """
        self._options['shift_end'] = value

    # -----------------------------------------------------------------------
    # Annotate
    # -----------------------------------------------------------------------

    def _set_meta(self, filler, tier):
        """Set meta values to the tier."""
        tier.set_meta('threshold_volume', str(filler.get_vol_threshold()))
        tier.set_meta('minimum_silence_duration', str(filler.get_min_sil_dur()))
        tier.set_meta('minimum_ipus_duration', str(filler.get_min_ipu_dur()))
        tier.set_meta('shift_ipus_start', str(filler.get_shift_start()))
        tier.set_meta('shift_ipus_end', str(filler.get_shift_end()))

        self.logfile.print_message(_info(1058), indent=1)
        m1 = _info(1290).format(filler.get_vol_threshold())
        m2 = _info(1292).format(filler.get_min_sil_dur())
        m3 = _info(1294).format(filler.get_min_ipu_dur())
        for m in (m1, m2, m3):
            self.logfile.print_message(m, indent=2)

    # -----------------------------------------------------------------------

    def convert(self, channel, text_tier):
        """Return a tier with transcription aligned to the audio.

        :param channel: (sppasChannel) Input audio channel
        :param text_tier: (sppasTier) Input transcription text in a PointTier

        """
        units = list()
        for a in text_tier:
            units.append(serialize_labels(a.get_labels()))
        ipus = [unit for unit in units if unit != SIL_ORTHO]

        # Create the instance to fill in IPUs
        filler = FillIPUs(channel, units)
        filler.set_min_ipu(self._options['min_ipu'])
        filler.set_min_sil(self._options['min_sil'])
        filler.set_shift_start(self._options['shift_start'])
        filler.set_shift_end(self._options['shift_end'])

        n = filler.fix_threshold_durations()
        if n != len(ipus):
            return

        # Process the data
        tracks = filler.get_tracks(time_domain=True)
        tier = sppasSearchIPUs.tracks_to_tier(
            tracks,
            channel.get_duration(),
            filler.get_vagueness()
        )
        tier.set_name('Transcription')
        self._set_meta(filler, tier)
        i = 0
        for a in tier:
            if a.get_best_tag().is_silence() is False:
                a.set_labels([sppasLabel(sppasTag(ipus[i]))])
                i += 1

        return tier

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
                    raise AudioChannelError(n)
                idx = audio_speech.extract_channel()
                channel = audio_speech.get_channel(idx)
                audio_filename = filename
                audio_speech.close()

            elif tier is None and fe in annot_ext:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                # a raw transcription is expected. "raw" must be in the name.
                tier = sppasFindTier.transcription(trs_input)
                if "raw" not in tier.get_name().lower():
                    tier = None

        # Check input tier
        if tier is None:
            logging.error("A tier with the raw transcription was not found.")
            raise NoTierInputError
        if tier.is_point() is False:
            logging.error("The tier with the raw transcription should be of type: Point.")
            raise AnnDataTypeError(tier.get_name(), 'PointTier')
        if tier.is_empty() is True:
            raise EmptyInputError(tier.get_name())

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

    # -----------------------------------------------------------------------
    # Apply the annotation on one or several given files
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        input_filename is a tuple (audio, raw transcription)

        :param input_files: (list of str) (audio, ortho)
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        input_channel, input_tier = self.get_inputs(input_files)

        # Get the framerate of the audio file
        framerate = input_channel.get_framerate()

        # Fill in the IPUs
        tier = self.convert(input_channel, input_tier)
        if tier is None:
            self.logfile.print_message(_info(1296), indent=2, status=-1)
            return None

        # Create the transcription to put the result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta("media_sample_rate", str(framerate))
        trs_output.set_meta('annotation_result_of', input_files[0])
        trs_output.append(tier)
        tier.set_media(input_tier.get_media())

        # Save in a file
        if output is not None:
            output_file = self.fix_out_file_ext(output)
            parser = sppasTrsRW(output_file)
            parser.write(trs_output)
            return [output_file]

        return trs_output

    # -----------------------------------------------------------------------

    def run_for_batch_processing(self, input_files):
        """Perform the annotation on a file.

        This method is called by 'batch_processing'. It fixes the name of the
        output file, and call the run method.

        Override to NOT ANNOTATE if an annotation is already existing.

        :param input_files: (list of str) the required inputs for a run
        :returns: output file name or None

        """
        # Fix the output file name
        root_pattern = self.get_out_name(input_files[0])

        # Is there already an existing IPU-seg (in any format)!
        ext = []
        for e in sppasTrsRW.annot_extensions():
            if e not in ('.txt', ):
                ext.append(e)
        exists_out_name = sppasBaseAnnotation._get_filename(root_pattern, ext)

        # it's existing... but not in the expected format: we convert!
        new_files = list()
        if exists_out_name is not None:
            out_name = self.fix_out_file_ext(root_pattern)
            if exists_out_name.lower() == out_name.lower():
                return list()

            else:
                try:
                    parser = sppasTrsRW(exists_out_name)
                    t = parser.read()
                    parser.set_filename(out_name)
                    parser.write(t)
                    self.logfile.print_message(_info(1302).format(out_name), indent=2, status=annots.info)
                    return [out_name]
                except:
                    pass
        else:
            # Create annotation instance, fix options, run.
            try:
                new_files = self.run(input_files, root_pattern)
            except Exception as e:
                self.logfile.print_message(
                    "{:s}\n".format(str(e)), indent=1, status=-1)

        return new_files

    # ----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "")

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Pattern this annotation expects for its input filename."""
        return [
            self._options.get("inputpattern1", ""),  # audio
            self._options.get("inputpattern2", "")   # text
            ]

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename."""
        return [
            SppasFiles.get_informat_extensions("AUDIO"),
            [".txt"]
            ]
