# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.buttons.textbutton.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Our custom button with a label text.

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

import wx
import random
import logging

from .basebutton import sb
from .basebutton import BaseButton

# ---------------------------------------------------------------------------


class TextButton(BaseButton):
    """TextButton is a custom button with a label.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseButton => TextButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label="",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param label: label text of the check button;
        :param pos: the position;
        :param size: the size;
        :param name: the name of the bitmap.

        """
        self._label = label
        self._align = wx.ALIGN_CENTER  # or ALIGN_LEFT or ALIGN_RIGHT

        super(TextButton, self).__init__(parent, id, pos, size, name)

    # ------------------------------------------------------------------------

    def GetLabel(self):
        """Return the label text as it was passed to SetLabel."""
        return self._label

    # ------------------------------------------------------------------------

    def SetLabel(self, label):
        """Set the label text.

        :param label: (str) Label text.

        """
        if label is None:
            label = ""
        self._label = str(label)

    # -----------------------------------------------------------------------

    def GetAlign(self):
        """Return the alignment of the label in the button."""
        return self._align

    # -----------------------------------------------------------------------

    def SetAlign(self, align=wx.ALIGN_CENTER):
        """Set the alignment of the label in the button.

        :param align: (int) label is at the center, at left or at right.

        """
        if align not in [wx.ALIGN_CENTER, wx.ALIGN_LEFT, wx.ALIGN_RIGHT]:
            return
        self._align = align

    # -----------------------------------------------------------------------

    Label = property(GetLabel, SetLabel)
    Align = property(GetAlign, SetAlign)

    # -----------------------------------------------------------------------

    def DoGetBestSize(self):
        """Overridden base class virtual.

        Determines the best size of the button based on the label.

        """
        label = self.GetLabel()
        if not label:
            return wx.Size(self._min_width, self._min_height)

        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        ret_width, ret_height = dc.GetTextExtent(label)

        ret_width += (2 * self._vert_border_width)
        ret_height += (2 * self._horiz_border_width)

        width = int(max(ret_width, ret_height) * 1.5)
        return wx.Size(width, width)

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """Draw the button. """
        x, y, w, h = self.GetContentRect()
        tw, th = self.get_text_extend(dc, gc, self._label)

        # min height to draw the label.
        # we authorize the font to be 20% truncated in height
        min_height = int(float(self.get_font_height()) * 0.8)
        if tw < min_height or th < min_height:
            return

        if self._align == wx.ALIGN_LEFT:
            self._draw_label(dc, gc, self._vert_border_width, ((h - th) // 2) + self._horiz_border_width)

        elif self._align == wx.ALIGN_RIGHT:
            self._draw_label(dc, gc, w - tw - self._vert_border_width, ((h - th) // 2) + self._horiz_border_width)

        else:
            # Center the text.
            self._draw_label(dc, gc, (w - tw) // 2, ((h - th) // 2) + self._horiz_border_width)

    # -----------------------------------------------------------------------

    def _draw_label(self, dc, gc, x, y):
        font = self.GetFont()
        gc.SetFont(font)
        dc.SetFont(font)
        if wx.Platform == '__WXGTK__':
            dc.SetTextForeground(self.GetPenForegroundColour())
            dc.DrawText(self._label, x, y)
        else:
            gc.SetTextForeground(self.GetPenForegroundColour())
            gc.DrawText(self._label, x, y)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanelTextButton(wx.Panel):

    def __init__(self, parent):
        super(TestPanelTextButton, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test TextButton")

        bgpbtn = wx.Button(self, label="BG-panel", pos=(10, 10), size=(64, 64), name="bgp_color")
        bgbbtn = wx.Button(self, label="BG-buttons", pos=(110, 10), size=(64, 64), name="bgb_color")
        fgbtn = wx.Button(self, label="FG", pos=(210, 10), size=(64, 64), name="font_color")
        self.Bind(wx.EVT_BUTTON, self.on_bgp_color, bgpbtn)
        self.Bind(wx.EVT_BUTTON, self.on_bgb_color, bgbbtn)
        self.Bind(wx.EVT_BUTTON, self.on_fg_color, fgbtn)

        st = [wx.PENSTYLE_SHORT_DASH,
              wx.PENSTYLE_LONG_DASH,
              wx.PENSTYLE_DOT_DASH,
              wx.PENSTYLE_SOLID,
              wx.PENSTYLE_HORIZONTAL_HATCH]

        # play with the border
        # -------------------
        x = 10
        w = 100
        h = 50
        c = 10
        for i in range(1, 6):
            btn = TextButton(self, label="toto", pos=(x, 100), size=(w, h))
            btn.SetBorderWidth(i)
            btn.SetBorderColour(wx.Colour(c, c, c))
            btn.SetBorderStyle(st[i-1])
            c += 40
            x += w + 10

        # play with the focus
        # -------------------
        x = 10
        c = 10
        for i in range(1, 6):
            btn = TextButton(self, pos=(x, 170), size=(w, h))
            btn.SetBorderWidth(1)
            btn.SetFocusWidth(i)
            btn.SetFocusColour(wx.Colour(c, c, c))
            btn.SetFocusStyle(st[i-1])
            c += 40
            x += w + 10

        # play with H/V
        # -------------
        vertical = TextButton(self, pos=(560, 100), size=(50, 110))
        vertical.SetBackgroundColour(wx.Colour(128, 255, 196))

        # play with enabled/disabled and colors
        # -------------------------------------
        btn1 = TextButton(self, pos=(10, 230), size=(w, h))
        btn1.Enable(True)
        btn1.SetBorderWidth(1)
        btn1.SetLabel("Set label")

        btn2 = TextButton(self, label="Disabled!", pos=(150, 230), size=(w, h))
        btn2.Enable(False)
        btn2.SetBorderWidth(1)

        btn3 = TextButton(self, label="हैलो", pos=(290, 230), size=(w, h))
        btn3.Enable(True)
        btn3.SetBorderWidth(1)
        btn3.SetBackgroundColour(wx.Colour(222, 222, 200))
        btn3.SetForegroundColour(wx.Colour(22, 22, 20))

        btn4 = TextButton(self, label="dzień dobry", pos=(430, 230), size=(w, h))
        btn4.Enable(False)
        btn4.SetBorderWidth(1)
        btn4.SetBackgroundColour(wx.Colour(222, 222, 200))
        btn4.SetForegroundColour(wx.Colour(22, 22, 20))

        # play with alignment
        # -------------------------------------
        btn5 = TextButton(self, label="Centered", pos=(10, 340), size=(w, h))
        btn5.SetBorderWidth(1)
        btn5.SetAlign(wx.ALIGN_CENTER)

        btn6 = TextButton(self, label="Text at left", pos=(150, 340), size=(w, h))
        btn6.SetBorderWidth(1)
        btn6.SetAlign(wx.ALIGN_LEFT)

        btn7 = TextButton(self, label="Text at right", pos=(290, 340), size=(w, h))
        btn7.SetBorderWidth(1)
        btn7.SetAlign(wx.ALIGN_RIGHT)

        # ----
        # In order to replace the wx.EVT_BUTTON:
        self.Bind(sb.EVT_WINDOW_SELECTED, self._on_selected)
        self.Bind(sb.EVT_WINDOW_FOCUSED, self._on_focused)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def on_bgp_color(self, event):
        """Change BG color of the panel. It shouldn't change bg of buttons."""
        self.SetBackgroundColour(wx.Colour(
            random.randint(10, 250),
            random.randint(10, 250),
            random.randint(10, 250)
        ))
        self.Refresh()

    # -----------------------------------------------------------------------

    def on_bgb_color(self, event):
        """Change BG color of the buttons. A refresh is needed."""
        for child in self.GetChildren():
            if isinstance(child, TextButton):
                child.SetBackgroundColour(wx.Colour(
                    random.randint(10, 250),
                    random.randint(10, 250),
                    random.randint(10, 250)
                    ))
                child.Refresh()

    # -----------------------------------------------------------------------

    def on_fg_color(self, event):
        color = wx.Colour(
            random.randint(10, 250),
            random.randint(10, 250),
            random.randint(10, 250))
        self.SetForegroundColour(color)
        for c in self.GetChildren():
            c.SetForegroundColour(color)
        self.Refresh()

    # -----------------------------------------------------------------------

    def _on_selected(self, event):
        win = event.GetEventObject()
        is_selected = event.GetSelected()
        logging.debug("Button with name {:s} is selected: {}".format(win.GetName(), is_selected))

    # -----------------------------------------------------------------------

    def _on_focused(self, event):
        win = event.GetEventObject()
        is_focused = event.GetFocused()
        logging.debug("Button with name {:s} is focused: {}".format(win.GetName(), is_focused))
        if is_focused is True:
            win.SetFont(win.GetFont().MakeLarger())
        else:
            win.SetFont(win.GetFont().MakeSmaller())
