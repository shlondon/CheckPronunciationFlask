# -*- coding: UTF-8 -*-
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

    src.ui.phoenix.windows.datactrls.audiovalues.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import datetime

from sppas.src.utils import b
from sppas.src.audiodata.audioconvert import sppasAudioConverter

# ---------------------------------------------------------------------------


class AudioData(object):
    """Data structure to store audio data values.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    """

    def __init__(self):
        # About the audio content itself.
        self.sampwidth = 0
        self.nchannels = 0
        self.framerate = 0
        self.duration = 0.
        self.frames = b("")

        # About what we need to draw if we have a period of time
        self.fperiod = (0, 0)
        self.values = dict()

    # -----------------------------------------------------------------------

    def set_period(self, start_time, end_time, nb_steps=7680):
        """

        :param nb_steps: (int) Number of expected values (7680 = 2*4K width)

        """
        # Convert the time (in seconds) into a position in the frames
        start_pos = self._time_to_pos(start_time)
        end_pos = self._time_to_pos(end_time)
        self.fperiod = (start_pos, end_pos)

        # Evaluate all values during this period, with a given nb of steps
        self._extract_values(nb_steps)

    # -----------------------------------------------------------------------

    def _extract_values(self, nb_steps):
        """Extract values from the frames.

        """
        all_frames = self._period_frames()
        if len(all_frames) == 0:
            return

        # the number of "values" we have
        nb_in_period = len(all_frames) // (self.sampwidth*self.nchannels)

        # if less than 1 frame by step... nb_steps is larger than our sampling rate
        if nb_in_period < nb_steps:
            nb_steps = nb_in_period
            nb_by_step = 1
        else:
            nb_by_step = (nb_in_period // nb_steps)

        # prepare memory -- faster then appending at each step
        self.values = dict()
        for c in range(self.nchannels):
            self.values[c] = [list()]*4
            self.values[c][0] = [0] * nb_steps
            self.values[c][1] = [0] * nb_steps
            self.values[c][2] = [0] * nb_steps
            self.values[c][3] = [0] * nb_steps

        started_time = datetime.datetime.now()
        for i in range(nb_steps):

            cur_pos = i * nb_by_step * self.sampwidth * self.nchannels
            next_pos = (i+1) * nb_by_step * self.sampwidth * self.nchannels
            frames = all_frames[cur_pos:next_pos]

            # convert frames into samples
            # -- it's much more faster than getting min/max from the frames
            samples = sppasAudioConverter().unpack_data(frames, self.sampwidth, self.nchannels)
            for c in range(self.nchannels):
                self.values[c][0][i] = len(samples)
                self.values[c][1][i] = min(samples[c])
                self.values[c][2][i] = max(samples[c])
                self.values[c][3][i] = self._zero_crossing(samples[c])

        cur_time = datetime.datetime.now()
        delta = cur_time - started_time
        delta_seconds = delta.seconds + delta.microseconds / 1000000.

    # -----------------------------------------------------------------------

    @staticmethod
    def _zero_crossing(samples):
        """Return the number of zero-crossing in the given samples.

        A zero-crossing occurs if successive samples have different algebraic
        signs.

        """
        if len(samples) < 2:
            return 0
        nz = 0
        i = 1
        negative = samples[0] < 0
        nb_samples = len(samples)
        while i < nb_samples:
            if negative:
                while samples[i] < 0:
                    i += 1
                    if i == nb_samples:
                        return nz
            else:
                while samples[i] >= 0:
                    i += 1
                    if i == nb_samples:
                        return nz

            nz += 1
            negative = not negative

    # -----------------------------------------------------------------------

    def _time_to_pos(self, time_value):
        return int(time_value * float(self.framerate)) * \
               self.sampwidth * \
               self.nchannels

    # -----------------------------------------------------------------------

    def _period_frames(self):
        """Return the frame of the currently defined period."""
        if self.fperiod[1] - self.fperiod[0] > 0:
            frames = self.frames[self.fperiod[0]:self.fperiod[1]]
        else:
            frames = b('')
        return frames
