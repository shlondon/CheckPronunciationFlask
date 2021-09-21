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

    src.ui.phoenix.windows.datactrls.waveform.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A window to draw the amplitude of a fragment of a channel.

"""

import os
import wx

from sppas.src.config import paths
from sppas.src.audiodata.aio import open as audio_open
from sppas.src.audiodata import sppasAudioFrames

from sppas.src.ui.phoenix.windows import sppasDCWindow
from .audiovalues import AudioData

# ---------------------------------------------------------------------------


class sppasWaveformWindow(sppasDCWindow):
    """A base window with a DC to draw amplitude of a channel of an audio.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    """

    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.BORDER_NONE | wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
                 name="waveform"):
        """Initialize a new sppasWaveformWindow instance.

        :param parent: Parent window. Must not be None.
        :param id:     A value of -1 indicates a default value.
        :param pos:    If the position (-1, -1) is specified
                       then a default position is chosen.
        :param size:   If the default size (-1, -1) is specified
                       then a default size is chosen.
        :param style:  often LC_REPORT
        :param name:   Window name.

        """
        super(sppasWaveformWindow, self).__init__(parent, id, pos, size, style, name)
        self._vert_border_width = 0
        self._horiz_border_width = 0

        # Adjust automatically the height of the amplitude
        self._auto_scroll = False

        # Style of the waveform: lines or bars
        self._pen_width = 1
        self._draw_style = "lines"

        # An instance of AudioData()
        self._data = None

        # The amplitude values (min-max) to draw for each step value
        self._datastep = dict()
        self._oversampled = False

        self.Bind(wx.EVT_SIZE, self._on_size)

    # -----------------------------------------------------------------------

    def _on_size(self, event):
        # in case the width has changed, re-calculate the values of each step
        self.__reset_datastep()
        self.Refresh()

    # -----------------------------------------------------------------------
    # How the waveform will look...
    # -----------------------------------------------------------------------

    def SetLineStyle(self, style="lines"):
        """Set the draw style: lines or bars."""
        if style not in ("lines", "bars"):
            style = "lines"
        self._draw_style = style

    # -----------------------------------------------------------------------

    def SetPenWidth(self, value):
        value = int(value)
        if value < 1:
            value = 1
        if value > 20:
            value = 20
        self._pen_width = value

    # -----------------------------------------------------------------------

    def SetAutoScroll(self, value):
        value = bool(value)
        if value != self._auto_scroll:
            self._auto_scroll = value
            self.__reset_minmax()

    # -----------------------------------------------------------------------
    # Samples to draw
    # -----------------------------------------------------------------------

    def set_audiodata(self, audiodata):
        """Set the audio with the pre-evaluated values for a fixed number of steps.

        To draw the waveform, we are interested in the second (min) and
        third (max) values of the data.

        """
        self._data = audiodata
        self.__reset_minmax()
        self.__reset_datastep()

    # -----------------------------------------------------------------------

    def __reset_minmax(self):
        # Min and max amplitude values for this sampwidth (2=>32k)
        self._data_max = sppasAudioFrames().get_maxval(self._data.sampwidth)
        self._data_min = -self._data_max

        # Min and max amplitude values observed in the samples of the period
        if self._auto_scroll is True:
            min_val, max_val = self.__get_minmax_values()

            # autoscroll is limited to at least 10% of what is possible
            # and the same range for all channels
            self._data_max = int(max(float(max_val) * 1.1, float(self._data_max) * 0.1))
            self._data_min = int(min(float(min_val) * 1.1, float(self._data_min) * 0.1))

    # -----------------------------------------------------------------------

    def __get_minmax_values(self):
        """Min and max amplitude values observed in the samples of the period."""
        min_val = sppasAudioFrames().get_maxval(self._data.sampwidth)
        max_val = -self._data_max
        for c in range(len(self._data.values)):
            if len(self._data.values[c][1]) > 0:
                min_val_channel = min(self._data.values[c][1])
                if min_val_channel < min_val:
                    min_val = min_val_channel
            if len(self._data.values[c][2]) > 0:
                max_val_channel = max(self._data.values[c][2])
                if max_val_channel > max_val:
                    max_val = max_val_channel

        return min_val, max_val

    # -----------------------------------------------------------------------

    def __reset_datastep(self):
        self._datastep = dict()
        if self._data is None:
            return
        if len(self._data.values) < self._data.nchannels:
            return

        # Fill in the data of each step.
        # They depend on the view: bars, lines, oversampled
        x, y, w, h = self.GetContentRect()
        if len(self._data.values[0][0]) > w:
            self._oversampled = False
            # There are more values than pixels
            for c in range(self._data.nchannels):
                self._datastep[c] = list()

            if self._draw_style == "lines":
                xstep = self._pen_width
            else:
                xstep = self._pen_width + (self._pen_width // 3)
            x += (xstep // 2)

            for c in range(self._data.nchannels):
                xcur = x
                coeff = float(len(self._data.values[c][0])) / float(w)
                while xcur < (x + w):
                    # the range of values we'll use for this xcur
                    dcur = int(float(xcur - x) * coeff)
                    dnext = int(float(xcur + xstep - x) * coeff)
                    self._datastep[c].append((xcur,
                                              min(self._data.values[c][1][dcur:dnext]),
                                              max(self._data.values[c][2][dcur:dnext])))

                    # next step
                    xcur += xstep
        else:
            self._oversampled = True

    # -----------------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Draw the amplitude values as a waveform."""
        if self._data is None:
            return
        if self._data.nchannels < 1:
            return

        x, y, w, h = self.GetContentRect()
        ch = h // self._data.nchannels

        for i in range(self._data.nchannels):
            # Draw horizontal lines
            self.__draw_horiz_axes(dc, gc, x, y + (i*ch), w, ch)
            # Draw the i-th channel in the given rectangle.
            if self._oversampled is False:
                if len(self._datastep[i]) > 0:
                    # Draw amplitude values either with bars or continuous lines
                    if self._draw_style == "bars":
                        self.__draw_amplitude_as_bars(i, dc, x, y + (i*ch), w, ch)
                    else:
                        self.__draw_amplitude_as_lines(i, dc, x, y + (i*ch), w, ch)
            else:
                # More pixels than values to draw... i.e. high zoom level.
                self.__draw_amplitude_oversampled(i, dc, x, y + (i*ch), w, ch)

    # -----------------------------------------------------------------------

    def __draw_horiz_axes(self, dc, gc, x, y, w, h):
        """Draw an horizontal line at the middle (indicate 0 value). """
        p = h // 100
        y_center = y + (h // 2)
        pen = wx.Pen(wx.Colour(128, 128, 212, 128), p, wx.PENSTYLE_SOLID)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)

        # Line at the centre
        th, tw = self.get_text_extend(dc, gc, "-0.0")
        dc.DrawLine(x, y_center, x + w, y_center)
        self.DrawLabel("0", dc, gc, x, y_center - (th // 3))

        if self._auto_scroll is False:
            # Lines at top and bottom
            dc.DrawLine(x, y + (p//2), x + w, y + (p//2))
            dc.DrawLine(x, h - (p//2), x + w, h - (p//2))

            # Scale at top and bottom
            self.DrawLabel("1", dc, gc, x, y)
            self.DrawLabel("-1", dc, gc, x, h - (th//2))

            if h > 200:
                pen = wx.Pen(wx.Colour(128, 128, 212, 196), 1, wx.PENSTYLE_DOT)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                dc.DrawLine(x, h//4, x + w, h//4)
                dc.DrawLine(x, y_center + h//4, x + w, y_center + h//4)

        else:
            if len(self._data.frames) > 0:
                pen = wx.Pen(wx.Colour(128, 128, 212, 196), 2, wx.PENSTYLE_DOT)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                # the height we should use to draw the whole scale
                audio_data_max = sppasAudioFrames().get_maxval(self._data.sampwidth)
                min_val, max_val = self.__get_minmax_values()
                viewed_ratio = float(max_val) / float(audio_data_max)
                viewed_ratio = round(viewed_ratio, 1)
                value = viewed_ratio * float(audio_data_max)

                # Lines at top and bottom
                ypixels = int(value * (float(h) / 2.0) / float(self._data_max))
                dc.DrawLine(x, y_center - ypixels, x + w, y_center - ypixels)
                self.DrawLabel(str(viewed_ratio), dc, gc, x, y_center - ypixels - (th // 3))

                dc.DrawLine(x, y_center + ypixels, x + w, y_center + ypixels)
                self.DrawLabel(str(-viewed_ratio), dc, gc, x, y_center + ypixels - (th // 3))

    # -----------------------------------------------------------------------

    def __draw_amplitude_as_lines(self, channel, dc, x, y, w, h):
        """Draw the waveform as joint lines.

        Current min/max observed values are joint to the next ones by a
        line. It looks like an analogic signal more than a discrete one.

        """
        y_center = y + (h // 2)
        ypixelsminprec = y_center

        # Fix the pen style and color
        pen = wx.Pen(self.GetPenForegroundColour(), self._pen_width, wx.PENSTYLE_SOLID)
        dc.SetPen(pen)

        for step in range(len(self._datastep[channel])):

            (xcur, datamin, datamax) = self._datastep[channel][step]

            # Convert the data into a "number of pixels" -- height
            ypixelsmax = int(float(datamax) * (float(h) / 2.0) / float(self._data_max))
            if self._data_min != 0:
                ypixelsmin = int(float(datamin) * (float(h) / 2.0) / float(abs(self._data_min)))
            else:
                ypixelsmin = 0

            # draw a line between prec. value to current value
            if xcur != x:
                dc.DrawLine(xcur, y_center - ypixelsminprec, xcur, y_center - ypixelsmax)
                if step+1 < len(self._datastep[channel]):
                    (xnext, datamin, datamax) = self._datastep[channel][step+1]
                    dc.DrawLine(xnext, y_center - ypixelsmin, xnext, y_center - ypixelsmax)

            ypixelsminprec = ypixelsmin

    # -----------------------------------------------------------------------

    def __draw_amplitude_as_bars(self, channel, dc, x, y, w, h):
        """Draw the waveform as vertical bars.

        Current min/max observed values are drawn by a vertical line.

        """
        y_center = y + (h // 2)

        # Fix the pen style and color
        pen = wx.Pen(self.GetPenForegroundColour(), self._pen_width, wx.PENSTYLE_SOLID)
        dc.SetPen(pen)

        for step in range(len(self._datastep[channel])):

            (xcur, datamin, datamax) = self._datastep[channel][step]

            # Convert the data into a "number of pixels" -- height
            ypixelsmax = int(float(datamax) * (float(h) / 2.0) / float(self._data_max))
            if self._data_min != 0:
                ypixelsmin = int(float(datamin) * (float(h) / 2.0) / float(abs(self._data_min)))
            else:
                ypixelsmin = 0

            # draw a vertical line
            if xcur != x:
                dc.DrawLine(xcur, y_center - ypixelsmax, xcur, y_center - ypixelsmin)

    # -----------------------------------------------------------------------

    def __draw_amplitude_oversampled(self, channel, dc, x, y, w, h):
        """Draw the data with vertical lines.

        Apply only if there are less data values than pixels to draw them.

        """
        nb_values = len(self._data.values[channel][1])
        y_center = y + (h // 2)
        xstep = round(float(w * 1.5) / float(nb_values))
        x += (xstep // 2)
        xcur = x

        while (xcur + xstep) < (x + w):
            coeff = float(nb_values) / float(w)

            # Get value of n samples between xcur and xnext
            dcur = int(float(xcur - x) * coeff)
            dnext = int(float(xcur + xstep - x) * coeff)
            data = self._data.values[channel][1][dcur:dnext]

            for value in data:
                pen = wx.Pen(self.GetPenForegroundColour(), 1, wx.PENSTYLE_SOLID)
                dc.SetPen(pen)
                if value > 0:
                    # convert the data into a "number of pixels" -- height
                    y_pixels = int(float(value) * (float(h) / 2.0) / float(self._data_max))
                else:
                    y_pixels = int(float(value) * (float(h) / 2.0) / float(abs(self._data_min)))

                if xstep > 1:
                    point_size = xstep
                    dc.DrawLine(xcur, y_center, xcur, y_center - y_pixels)
                else:
                    point_size = 3

                pen = wx.Pen(self.GetPenForegroundColour(), point_size, wx.PENSTYLE_SOLID)
                dc.SetPen(pen)
                dc.DrawPoint(xcur, y_center - y_pixels)

            xcur += xstep

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test Waveform")

        sample = os.path.join(paths.samples, "samples-eng", "oriana1.wav")   # mono
        self._audio = audio_open(sample)

        w0 = self.__draw_waveform(0., 90.)

        w1 = self.__draw_waveform(2., 3.)
        w1.SetPenWidth(9)
        w1.SetLineStyle("bars")
        w1.SetAutoScroll(True)

        w2 = self.__draw_waveform(2.56, 2.60)

        sample_stereo = os.path.join(paths.samples, "samples-eng", "oriana3.wave")
        self._audios = audio_open(sample_stereo)
        ws = self.__draw_stereo_waveform(0., 90.)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(w0, 1, wx.EXPAND)
        sizer.Add(w1, 1, wx.EXPAND)
        sizer.Add(w2, 1, wx.EXPAND)
        sizer.Add(ws, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def __draw_waveform(self, start_time, end_time):
        audiodata = AudioData()
        audiodata.sampwidth = self._audio.get_sampwidth()
        audiodata.nchannels = self._audio.get_nchannels()
        audiodata.framerate = self._audio.get_framerate()
        audiodata.frames = self._audio.read_frames(self._audio.get_nframes())
        self._audio.seek(0)
        audiodata.set_period(start_time, end_time)

        w = sppasWaveformWindow(self)
        w.set_audiodata(audiodata)
        return w

    def __draw_stereo_waveform(self, start_time, end_time):
        audiodata = AudioData()
        audiodata.sampwidth = self._audios.get_sampwidth()
        audiodata.nchannels = self._audios.get_nchannels()
        audiodata.framerate = self._audios.get_framerate()
        audiodata.frames = self._audios.read_frames(self._audios.get_nframes())
        audiodata.set_period(start_time, end_time)

        w = sppasWaveformWindow(self)
        w.set_audiodata(audiodata)
        return w

