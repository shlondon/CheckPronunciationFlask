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

    src.ui.phoenix.windows.popup.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import wx

from .buttonbox import sppasCheckBoxPanel
from .buttonbox import sppasToggleBoxPanel

# ---------------------------------------------------------------------------


class PopupLabel(wx.PopupTransientWindow):
    """A popup window to display a simple text.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    The popup is destroyed when it is clicked in.

    """

    def __init__(self, parent, style, label):
        wx.PopupTransientWindow.__init__(self, parent, style)
        pnl = wx.Panel(self, name="main_panel")

        try:
            s = wx.GetApp().settings
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

        pnl.SetBackgroundColour("YELLOW")
        pnl.SetForegroundColour("BLACK")

        border = PopupLabel.fix_size(10)

        st = wx.StaticText(pnl, -1, label, pos=(border//2, border//2))
        sz = st.GetBestSize()
        self.SetSize((sz.width + border, sz.height + border))
        pnl.SetSize((sz.width + border, sz.height + border))

        pnl.Bind(wx.EVT_LEFT_UP, self._on_mouse_up)
        pnl.Bind(wx.EVT_RIGHT_UP, self._on_mouse_up)
        st.Bind(wx.EVT_LEFT_UP, self._on_mouse_up)
        st.Bind(wx.EVT_RIGHT_UP, self._on_mouse_up)

        wx.CallAfter(self.Refresh)

    # -----------------------------------------------------------------------

    @staticmethod
    def fix_size(value):
        """Return a proportional size value.

        :param value: (int)
        :returns: (int)

        """
        try:
            obj_size = int(float(value) * wx.GetApp().settings.size_coeff)
        except AttributeError:
            obj_size = int(value)
        return obj_size

    # -----------------------------------------------------------------------

    @property
    def _pnl(self):
        return self.FindWindow("main_panel")

    # -----------------------------------------------------------------------

    def _on_mouse_up(self, evt):
        self.Show(False)
        wx.CallAfter(self.Destroy)

# ---------------------------------------------------------------------------


class PopupToggleBox(wx.PopupWindow):
    """A popup window embedding a sppasToggleBoxPanel.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    The parent can bind wx.EVT_COMBOBOX.
    The sppasComboBox is not editable.

    The popup has to be destroyed externally.

    """

    def __init__(self, parent, choices):
        """Constructor"""
        wx.PopupWindow.__init__(self, parent)

        sizer = wx.BoxSizer()
        tglbox = sppasToggleBoxPanel(self, choices=choices, majorDimension=1, name="togglebox")
        tglbox.SetVGap(0)
        tglbox.SetHGap(0)
        sizer.Add(tglbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)

        # Look&feel
        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

        self.SetMinSize(tglbox.GetSize())
        self.SetSizerAndFit(sizer)
        wx.CallAfter(self.Refresh)

    # ------------------------------------------------------------------------

    @property
    def tglbox(self):
        return self.FindWindow("togglebox")

    # ------------------------------------------------------------------------

    def SetBackgroundColour(self, color):
        wx.Dialog.SetBackgroundColour(self, color)
        self.tglbox.SetBackgroundColour(color)

    def SetForegroundColour(self, color):
        wx.Dialog.SetForegroundColour(self, color)
        self.tglbox.SetForegroundColour(color)

    def SetFont(self, font):
        wx.Dialog.SetFont(self, font)
        self.tglbox.SetFont(font)

    # ------------------------------------------------------------------------

    def UpdateSize(self):
        size = self.tglbox.GetSize()
        self.SetSize(size)

# ---------------------------------------------------------------------------


class PopupCheckBox(wx.PopupTransientWindow):
    """A popup window embedding a sppasCheckBoxPanel.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    The parent can bind wx.EVT_CHECKBOX.

    """

    def __init__(self, parent, choices):
        """Constructor"""
        wx.PopupTransientWindow.__init__(self, parent)

        sizer = wx.BoxSizer()
        box = sppasCheckBoxPanel(self, choices=choices, majorDimension=1, name="checkbox")
        box.SetVGap(0)
        box.SetHGap(0)
        sizer.Add(box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)

        # Look&feel
        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

        self.SetMinSize(box.DoGetBestSize())
        self.SetSizerAndFit(sizer)
        wx.CallAfter(self.Refresh)

    # ------------------------------------------------------------------------

    @property
    def checkbox(self):
        return self.FindWindow("checkbox")

    # ------------------------------------------------------------------------

    def SetBackgroundColour(self, color):
        wx.Dialog.SetBackgroundColour(self, color)
        self.checkbox.SetBackgroundColour(color)

    def SetForegroundColour(self, color):
        wx.Dialog.SetForegroundColour(self, color)
        self.checkbox.SetForegroundColour(color)

    def SetFont(self, font):
        wx.Dialog.SetFont(self, font)
        self.checkbox.SetFont(font)

    # ------------------------------------------------------------------------

    def UpdateSize(self):
        size = self.checkbox.GetSize()
        self.SetSize(size)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Popup windows")

        b1 = wx.Button(self, -1, pos=(10, 10), label="Label Popup", name="label")
        b1.Bind(wx.EVT_BUTTON, self._on_button)

        b2 = wx.Button(self, -1, pos=(10, 50), label="Toggle Popup", name="toggle")
        b2.Bind(wx.EVT_BUTTON, self._on_button)
        self._tgl_popup = PopupToggleBox(b2, choices=["choice 1", "choice 2"])
        self._tgl_popup.Bind(wx.EVT_MOUSE_EVENTS, self._toggle_mouse_event)

        b3 = wx.Button(self, -1, pos=(10, 90), label="Check Popup", name="check")
        b3.Bind(wx.EVT_BUTTON, self._on_button)
        self._check_popup = PopupCheckBox(b3, choices=["choice 1", "choice 2"])
        self._check_popup.Bind(wx.EVT_MOUSE_EVENTS, self._check_mouse_event)

    # ------------------------------------------------------------------------

    def _on_button(self, event):
        evt_obj = event.GetEventObject()

        if evt_obj.GetName() == "label":
            text = "The label text that we're reading"
            # Open a "window" to show the label
            win = PopupLabel(self.GetTopLevelParent(), wx.SIMPLE_BORDER, text)
            # Show the popup right below or above the button
            # depending on available screen space...
            pos = evt_obj.ClientToScreen((0, 0))
            # the label popup will hide the button.
            win.Position(pos, (0, 0))
            win.Show(True)

        elif evt_obj.GetName() == "toggle":
            w, h = self.GetClientSize()
            dw, dh = wx.DisplaySize()
            pw, ph = self._tgl_popup.tglbox.DoGetBestSize()
            self._tgl_popup.SetSize(wx.Size(w, ph))
            # Get the absolute position of this toggle
            x, y = self.GetScreenPosition()
            if (y + h + ph) > dh:
                # popup at top
                self._tgl_popup.SetPosition(wx.Point(x, y - h))
            else:
                # popup at bottom
                self._tgl_popup.SetPosition(wx.Point(x, y + h))

            self._tgl_popup.Layout()
            self._tgl_popup.Show()
            self._tgl_popup.SetFocus()
            self._tgl_popup.Raise()

        elif evt_obj.GetName() == "check":
            # Get the absolute position of this toggle
            cw, ch = self.GetClientSize()
            w, h = self._check_popup.DoGetBestSize()

            mx, my = wx.GetMousePosition()
            # we need to get the mouse inside the popup
            cx = mx - (w // 3)
            self._check_popup.SetPosition(wx.Point(cx, my - (h // 3)))
            self._check_popup.SetSize(wx.Size(cw - cx, h))

            self._check_popup.Layout()
            self._check_popup.Show()
            self._check_popup.SetFocus()
            self._check_popup.Raise()

    # ------------------------------------------------------------------------

    def _toggle_mouse_event(self, event):
        if event.Leaving():
            self._tgl_popup.Hide()

    # ------------------------------------------------------------------------

    def _check_mouse_event(self, event):
        if event.Leaving():
            self._check_popup.Hide()
            wx.LogDebug("Checked choices: {}".format(self._check_popup.checkbox.GetSelection()))


