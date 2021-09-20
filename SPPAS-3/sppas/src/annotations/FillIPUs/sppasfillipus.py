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

from sppas.src.config import symbols
from sppas.src.config import info
from sppas.src.utils import u
import sppas.src.audiodata.aio
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasMedia
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from sppas.src.config import annots
import sppas.src.anndata.aio

from ..SearchIPUs.sppassearchipus import sppasSearchIPUs
from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import AudioChannelError
from ..baseannot import sppasBaseAnnotation

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

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
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

    def convert(self, input_audio_filename, input_filename):
        """Return a tier with transcription aligned to the audio.

        :param input_audio_filename: (str) Input audio file
        :param input_filename: (str) Input transcription file

        """
        # Get audio and the channel we'll work on
        audio_speech = sppas.src.audiodata.aio.open(input_audio_filename)
        n = audio_speech.get_nchannels()
        if n != 1:
            raise AudioChannelError(n)

        idx = audio_speech.extract_channel()
        channel = audio_speech.get_channel(idx)

        # Get the units we'll work on
        parser = sppasTrsRW(input_filename)
        trs = parser.read()
        if len(trs) > 1:
            pass
        if len(trs[0]) == 0:
            pass
        units = list()
        for a in trs[0]:
            units.append(serialize_labels(a.get_labels()))
        ipus = [u for u in units if u != SIL_ORTHO]

        # Create the instance to fill in IPUs
        filler = FillIPUs(channel, units)
        filler.set_min_ipu(self._options['min_ipu'])
        filler.set_min_sil(self._options['min_sil'])
        filler.set_shift_start(self._options['shift_start'])
        filler.set_shift_end(self._options['shift_end'])

        n = filler.fix_threshold_durations()
        if n != len(ipus):
            return

        # Process the data.
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
    # Apply the annotation on one or several given files
    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        input_filename is a tuple (audio, raw transcription)

        :param input_file: (list of str) (audio, ortho)
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        input_audio_filename = input_file[0]
        input_trans_filename = input_file[1]

        # Get the framerate of the audio file
        audio = sppas.src.audiodata.aio.open(input_file[0])
        framerate = audio.get_framerate()
        audio.close()

        # Fill in the IPUs
        tier = self.convert(input_audio_filename, input_trans_filename)
        if tier is None:
            self.logfile.print_message(_info(1296), indent=2, status=-1)
            return None

        # Create the transcription to put the result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta("media_sample_rate", str(framerate))
        trs_output.set_meta('fill_ipus_result_of', input_audio_filename)
        trs_output.set_meta('fill_ipus_result_of_trs', input_trans_filename)

        trs_output.append(tier)

        extm = os.path.splitext(input_audio_filename)[1].lower()[1:]
        media = sppasMedia(os.path.abspath(input_audio_filename),
                           mime_type="audio/"+extm)
        tier.set_media(media)

        # Save in a file
        if output is not None:
            output_file = self.fix_out_file_ext(output)
            parser = sppasTrsRW(output_file)
            parser.write(trs_output)
            return [output_file]

        return trs_output

    # -----------------------------------------------------------------------

    def run_for_batch_processing(self, input_file, opt_input_file):
        """Perform the annotation on a file.

        This method is called by 'batch_processing'. It fixes the name of the
        output file, and call the run method.
        Can be overridden.

        :param input_file: (list of str) the required input
        :param opt_input_file: (list of str) the optional input
        :returns: output file name or None

        """
        # Fix the output file name
        root_pattern = self.get_out_name(input_file[0])

        # Is there already an existing IPU-seg (in any format)!
        ext = []
        for e in sppas.src.anndata.aio.extensions_in:
            if e not in ('.txt', '.hz', '.PitchTier', '.IntensityTier'):
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
                new_files = self.run(input_file, opt_input_file, root_pattern)
            except Exception as e:
                self.logfile.print_message(
                    "{:s}\n".format(str(e)), indent=1, status=-1)

        return new_files

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename."""
        return sppas.src.audiodata.aio.extensions
