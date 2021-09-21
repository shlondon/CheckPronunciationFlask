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

    src.ui.phoenix.windows.slider.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a slider that is not built on native controls
    but is self-drawn.

"""

import wx
import os

from sppas.src.config import paths
from .basedcwindow import sppasImageDCWindow
from .panels import sppasPanel

# ---------------------------------------------------------------------------


class sppasSlider(sppasImageDCWindow):
    """A window imitating a slider but with the same look on all platforms.

     :author:       Brigitte Bigi
     :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
     :contact:      contact@sppas.org
     :license:      GPL, v3
     :copyright:    Copyright (C) 2011-2020 Brigitte Bigi

    Non-interactive: show values but can't be moved with the mouse.

    """

    POINT_COLOUR1 = wx.Colour(10, 60, 190)
    POINT_COLOUR2 = wx.Colour(40, 90, 220)
    POINT_COLOUR3 = wx.Colour(75, 125, 255)

    # -----------------------------------------------------------------------

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_NONE,
                 name="slider_panel"):
        """Create a self-drawn window to display a value into a range.

        """
        super(sppasSlider, self).__init__(parent, id, pos=pos, size=size, style=style, name=name)
        self._start = 0
        self._end = 0
        self.__pos = 0
        self._vert_border_width = 0
        self._horiz_border_width = 1
        self._min_width = 48

    # -----------------------------------------------------------------------

    def get_range(self):
        """Return the (start, end) values."""
        return self._start, self._end

    # -----------------------------------------------------------------------

    def set_range(self, start, end):
        """Fix the range of values the slider is considering.

        Do not refresh.

        :param start: (float)
        :param end: (float)
        :return: (float) current position: either the current one, start or end.

        """
        start = float(start)
        end = float(end)
        if start > end:
            raise ValueError("Start {} can't be greater then end {}".format(start, end))
        self._start = start
        self._end = end

        # question: do we have to adjust pos automatically??
        # if self.__pos < self._start:
        #     self.__pos = self._start
        # if self.__pos > self._end:
        #     self.__pos = self._end

    # -----------------------------------------------------------------------

    def get_value(self):
        """Return the current position value."""
        return self.__pos

    # -----------------------------------------------------------------------

    def set_value(self, pos):
        """Fix the current position value.

        Do not refresh.

        :param pos: (float) A position in the current range.
        :return: (float) current position: either the given one, start or end.

        """
        pos = float(pos)
        self.__pos = pos

        if self.__pos < self._start:
            self.__pos = self._start
        if self.__pos > self._end:
            self.__pos = self._end
        return self.__pos

    # -----------------------------------------------------------------------

    def formats_label(self, value):
        return str(value)

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Override."""
        self._DrawLabels(dc, gc)
        self._DrawMoment(dc, gc)

    # -----------------------------------------------------------------------

    def _DrawLabels(self, dc, gc):
        """Draw left-right values."""
        x, y, w, h = self.GetContentRect()

        # Start label
        label = self.formats_label(self._start)
        tw, th = self.get_text_extend(dc, gc, label)
        self.DrawLabel(label, dc, gc, 2, (h - th) // 2)

        # End label
        label = self.formats_label(self._end)
        tw, th = self.get_text_extend(dc, gc, label)
        self.DrawLabel(label, dc, gc, w - tw - 2, (h - th) // 2)

    # -----------------------------------------------------------------------

    def _DrawMoment(self, dc, gc):
        """Draw a vertical line to indicate the current position."""
        x, y, w, h = self.GetContentRect()

        # Draw the value of the current position at left or at right
        pos_x = 0
        total_dur = self._end - self._start
        pos_dur = self.__pos - self._start
        if total_dur > 0.:
            ratio = pos_dur / total_dur
            pos_x = w * ratio

        # Vertical line indicating the proportional position
        if total_dur > 0.:
            pen = wx.Pen(sppasSlider.POINT_COLOUR3, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x, y, pos_x, y+h)
            pen = wx.Pen(sppasSlider.POINT_COLOUR2, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x+1, y, pos_x+1, y+h)
            dc.DrawLine(pos_x-1, y, pos_x-1, y+h)
            pen = wx.Pen(sppasSlider.POINT_COLOUR1, 1, wx.PENSTYLE_SOLID)
            dc.SetPen(pen)
            gc.SetPen(pen)
            dc.DrawLine(pos_x+2, y, pos_x+2, y+h)
            dc.DrawLine(pos_x-2, y, pos_x-2, y+h)

# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    img = os.path.join(paths.etc, "images", "bg1.png")

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="Test Slider")

        s1 = sppasSlider(self, pos=(0, 0), size=wx.Size(120, 20), name="s1")

        s2 = sppasSlider(self, pos=(0, 50), size=wx.Size(120, 20), name="s2")
        s2.SetForegroundColour(wx.Colour(208, 200, 166))
        s2.SetBackgroundImage(TestPanel.img)
        s2.set_range(0, 10)
        s2.set_value(6)

        s3 = sppasSlider(self, style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_SIMPLE, name="s3")
        s3.set_range(0, 3245)
        s3.set_value(4567)

        s4 = sppasSlider(self, name="s4")
        s4.set_range(0, 345)
        s4.set_value(56)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(s1, 0, wx.EXPAND)
        s.Add(s2, 0, wx.EXPAND)
        s.Add(s3, 1, wx.EXPAND)
        s.Add(s4, 1, wx.EXPAND)
        self.SetSizer(s)
