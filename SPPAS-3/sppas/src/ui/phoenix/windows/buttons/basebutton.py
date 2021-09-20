# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.buttons.basebutton.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A self-drawn custom button with the focus follows mouse.

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

Description
===========

This module implements a base class of a generic button, meaning that it is
not built on native controls but is self-drawn.
It acts like a normal button except for the focus that is following the mouse.

Sample usage:
============

    import wx
    import buttons

    class appFrame(wx.Frame):
        def __init__(self, parent, title):

            wx.Frame.__init__(self, parent, wx.ID_ANY, title, size=(400, 300))
            panel = wx.Panel(self)
            btn = buttons.BaseButton(panel, -1, pos=(50, 50), size=(128, 32))

    app = wx.App()
    frame = appFrame(None, 'Button Test')
    frame.Show()
    app.MainLoop()

"""

import os
import wx
import logging

from sppas.src.config import paths   # paths is used in the TestPanel only

from ..basewindow import sppasWindow
from ..basewindow import WindowState
from ..winevents import sb
from ..winevents import sppasButtonPressedEvent

# ---------------------------------------------------------------------------


class BaseButton(sppasWindow):
    """A custom type of window to represent a button.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow => BaseButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    wx.PyCommandEvent - bind wx.EVT_BUTTON

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor.

        :param parent: (wx.Window) parent window. Must not be ``None``;
        :param id: (int) window identifier. A value of -1 indicates a default value;
        :param pos: the control position. A value of (-1, -1) indicates a default
         position, chosen by either the windowing system or wxPython, depending on
         platform;
        :param size: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param name: (str) Name of the button.

        """
        super(BaseButton, self).__init__(
            parent, id, pos, size,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
            name=name)

        # By default, our buttons don't have borders
        self._vert_border_width = 0
        self._horiz_border_width = 0

        self._min_width = 12
        self._min_height = 12

        # Setup Initial Size
        self.SetInitialSize(size)

    # ------------------------------------------------------------------------

    @staticmethod
    def get_text_extend(dc, gc, text):
        if wx.Platform == '__WXGTK__':
            return dc.GetTextExtent(text)
        return gc.GetTextExtent(text)

    # -----------------------------------------------------------------------

    def DrawBackground(self, dc, gc):
        """Draw the background with a color or transparent."""
        w, h = self.GetClientSize()

        brush = self.GetBackgroundBrush()
        if brush is not None:
            dc.SetBackground(brush)
            dc.Clear()

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(brush)
        dc.DrawRoundedRectangle(
            self._vert_border_width,
            self._horiz_border_width,
            w - (2 * self._vert_border_width),
            h - (2 * self._horiz_border_width),
            (self._vert_border_width + self._horiz_border_width) // 2)

    # -----------------------------------------------------------------------

    def DrawBorder(self, dc, gc):
        """Draw a gradient border with corners that appear slightly rounded.

        Notice that the transparency is not properly supported under Windows
        so that the borders won't have a gradient color!

        """
        w, h = self.GetClientSize()
        border_color = self.GetPenBorderColour()
        r = border_color.Red()
        g = border_color.Green()
        b = border_color.Blue()
        a = border_color.Alpha()

        shift = 1
        if wx.Platform == "__WXMAC__":
            shift = 0

        for i in reversed(range(self._vert_border_width)):
            # gradient border color, using transparency.
            alpha = max(a - (i * 25), 0)
            pen = wx.Pen(wx.Colour(r, g, b, alpha), 1, self._border_style)
            dc.SetPen(pen)

            # left line
            dc.DrawLine(i, self._horiz_border_width - i, i, h - self._horiz_border_width + i)
            # right line
            dc.DrawLine(w - i - shift, self._horiz_border_width - i, w - i - shift, h - self._horiz_border_width + i)

        for i in reversed(range(self._horiz_border_width)):
            # gradient border color, using transparency
            alpha = max(a - (i * 25), 0)
            pen = wx.Pen(wx.Colour(r, g, b, alpha), 1, self._border_style)
            dc.SetPen(pen)

            # upper line
            dc.DrawLine(self._vert_border_width - i, i, w - self._vert_border_width + i, i)
            # bottom line
            dc.DrawLine(self._vert_border_width - i, h - i - shift, w - self._vert_border_width + i, h - i - shift)

    # -----------------------------------------------------------------------

    def OnMouseLeftUp(self, event):
        """Handle the wx.EVT_LEFT_UP event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self.IsEnabled() is False:
            return

        # Mouse was down outside of the window but is up inside.
        if self.HasCapture() is False:
            return

        # Stop to redirect all mouse inputs to this window
        self.ReleaseMouse()

        # If the window was selected when the mouse was released...
        if self._state[1] == WindowState().selected:
            self._set_state(self._state[0])
            if self._state[1] != WindowState().selected:
                self.NotifySelected(value=False)
            if self._state[1] == WindowState().focused:
                self.NotifyFocused(value=True)

            # The mouse was selected by left-down then de-selected by left-up
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            evt.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(evt)

# ---------------------------------------------------------------------------


class BaseCheckButton(sppasWindow):
    """A custom type of window to represent a check button.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseCheckButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED
    wx.PyCommandEvent - bind wx.EVT_CHECKBOX

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.PanelNameStr):
        """Default class constructor.

        :param parent: (wx.Window) parent window. Must not be ``None``;
        :param id: (int) window identifier. A value of -1 indicates a default value;
        :param pos: the button position. A value of (-1, -1) indicates a default
         position, chosen by either the windowing system or wxPython, depending on
         platform;
        :param size: the button size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param name: (str) the button name.

        """
        super(BaseCheckButton, self).__init__(
            parent, id, pos, size,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
            name=name)

        # By default, our buttons don't have borders
        self._vert_border_width = 0
        self._horiz_border_width = 0

        self._min_width = 12
        self._min_height = 12
        self._pressed = False

        # Setup Initial Size
        self.SetInitialSize(size)

    # -----------------------------------------------------------------------

    def IsPressed(self):
        """Return if button is pressed.

        :returns: (bool)

        """
        return self._pressed

    # -----------------------------------------------------------------------

    def Check(self, value):
        if self._pressed != value:
            self._pressed = value
            if value:
                self._set_state(WindowState().selected)
            else:
                self._set_state(WindowState().normal)
            self.Refresh()

    # -----------------------------------------------------------------------
    # Override BaseButton
    # -----------------------------------------------------------------------

    def OnMouseLeftDown(self, event):
        """Handle the wx.EVT_LEFT_DOWN event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self.IsEnabled() is True:
            self._pressed = not self._pressed
            if self._pressed is False:
                self.NotifyPressed(self._pressed)

            # Direct all mouse inputs to this window
            self.CaptureMouse()
            if self._state[1] == WindowState().focused:
                self.NotifyFocused(value=False)

            self._set_state(WindowState().selected)
            if self._pressed is True:
                self.NotifySelected(value=True)

    # -----------------------------------------------------------------------

    def OnMouseLeftUp(self, event):
        """Handle the wx.EVT_LEFT_UP event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if not self.IsEnabled():
            return

        # Mouse was down outside of the button (but is up inside)
        if not self.HasCapture():
            return

        # Directs all mouse input to this window
        self.ReleaseMouse()

        # If the button was down when the mouse was released...
        if self._state[1] == WindowState().selected:
            if self._pressed is True:
                self._set_state(WindowState().selected)
                self.NotifyPressed(self._pressed)
            else:
                self._set_state(WindowState().focused)

            if self._state[1] != WindowState().selected:
                self.NotifySelected(value=False)

            # test self, in case the button was destroyed in the eventhandler
            if self._state[1] == WindowState().focused:
                self.NotifyFocused(value=True)

            # self.Refresh()  # done in set_state
            # event.Skip()
            # Notify only when this method is finished (in case the binder destroys us)
            self.NotifyWxButtonEvent()

    # ------------------------------------------------------------------------

    def NotifyWxButtonEvent(self):
        evt = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId, self.GetId())
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)

    # ------------------------------------------------------------------------

    def OnMouseLeave(self, event):
        """Handle the wx.EVT_LEAVE_WINDOW event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if not self.IsEnabled():
            return

        # Leave a pressed check-button
        if self._pressed is True:
            self._set_state(WindowState().selected)
            return

        if self._state[1] == WindowState().focused:
            self._set_state(WindowState().normal)
            self.NotifyFocused(value=False)
            event.Skip()

        elif self._state[1] == WindowState().selected:
            self._state[0] = WindowState().normal
            self.Refresh()
            event.Skip()

        self._pressed = False

    # -----------------------------------------------------------------------

    def NotifyPressed(self, value=True):
        evt = sppasButtonPressedEvent(self.GetId())
        evt.SetEventObject(self)
        evt.SetPressed(value)
        self.GetEventHandler().ProcessEvent(evt)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanelBaseButton(wx.Panel):

    def __init__(self, parent):
        super(TestPanelBaseButton, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="BaseButton & BaseCheckButton")

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
            btn = BaseButton(self, pos=(x, 10), size=(w, h))
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
            btn = BaseButton(self, pos=(x, 70), size=(w, h))
            btn.SetBorderWidth(1)
            btn.SetFocusWidth(i)
            btn.SetFocusColour(wx.Colour(c, c, c))
            btn.SetFocusStyle(st[i-1])
            c += 40
            x += w + 10

        # play with H/V
        # -------------
        vertical = BaseButton(self, pos=(560, 10), size=(50, 110))
        vertical.SetBackgroundColour(wx.Colour(128, 255, 196))

        # play with enabled/disabled and colors
        # -------------------------------------
        btn1 = BaseButton(self, pos=(10, 130), size=(w, h))
        btn1.Enable(True)
        btn1.SetBorderWidth(1)

        btn2 = BaseButton(self, pos=(150, 130), size=(w, h))
        btn2.Enable(False)
        btn2.SetBorderWidth(1)

        btn3 = BaseButton(self, pos=(290, 130), size=(w, h))
        btn3.Enable(True)
        btn3.SetBorderWidth(1)
        btn3.SetBackgroundColour(wx.Colour(222, 222, 200))
        btn3.SetForegroundColour(wx.Colour(22, 22, 20))

        btn4 = BaseButton(self, pos=(430, 130), size=(w, h))
        btn4.Enable(False)
        btn4.SetBorderWidth(1)
        btn4.SetBackgroundColour(wx.Colour(222, 222, 200))
        btn4.SetForegroundColour(wx.Colour(22, 22, 20))

        # ----

        img = os.path.join(paths.etc, "images", "bg6.png")
        wi2 = BaseCheckButton(self, pos=(10, 300), size=(50, 110), name="wi2")
        wi2.Enable(True)
        wi2.SetBackgroundImage(img)
        wi2.SetBorderColour(wx.Colour(128, 100, 66))

        img = os.path.join(paths.etc, "images", "trbg1.png")
        wi3 = BaseCheckButton(self, pos=(110, 300), size=(100, 100), name="wi3")
        wi3.Enable(True)
        wi3.SetBackgroundColour(wx.Colour(28, 200, 166))
        wi3.SetBackgroundImage(img)
        wi3.SetBorderColour(wx.Colour(128, 100, 66))
        wi3.SetBorderWidth(1)

        img = os.path.join(paths.samples, "faces", "BrigitteBigi_Aix2020.png")
        wi6 = BaseCheckButton(self, pos=(310, 280), size=(120, 150), name="wi6")
        wi6.SetBackgroundImage(img)
        wi6.SetBorderWidth(1)

        # ----
        btn_exit = BaseButton(self, pos=(200, 400), size=(100, 40), name="btn_exit")
        btn_exit.Enable(True)
        btn_exit.SetBorderWidth(3)
        btn_exit.SetBackgroundColour(wx.RED)
        btn_exit.SetForegroundColour(wx.Colour(222, 222, 220))
        btn_exit.Bind(wx.EVT_BUTTON, self._on_exit)

        # ----
        # In order to replace the wx.EVT_BUTTON:
        self.Bind(sb.EVT_WINDOW_SELECTED, self._on_selected)
        self.Bind(sb.EVT_WINDOW_FOCUSED, self._on_focused)
        self.Bind(wx.EVT_CHECKBOX, self._on_check)

    # -----------------------------------------------------------------------

    def _on_check(self, event):
        win = event.GetEventObject()
        # logging.debug("Button with name {:s} is checked.".format(win.GetName()))

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def _on_selected(self, event):
        win = event.GetEventObject()
        is_selected = event.GetSelected()
        # logging.debug("Button with name {:s} is selected: {}".format(win.GetName(), is_selected))

    # -----------------------------------------------------------------------

    def _on_exit(self, event):
        self.GetTopLevelParent().Destroy()

    # -----------------------------------------------------------------------

    def _on_focused(self, event):
        win = event.GetEventObject()
        is_focused = event.GetFocused()
        logging.debug("Button with name {:s} is focused: {}".format(win.GetName(), is_focused))
        if is_focused is True:
            win.SetFont(win.GetFont().MakeLarger())
        else:
            win.SetFont(win.GetFont().MakeSmaller())

    # -----------------------------------------------------------------------

    def _on_pressed(self, event):
        win = event.GetEventObject()
        is_pressed = event.GetPressed()
        logging.debug("CheckButton with name {:s} is pressed: {}".format(win.GetName(), is_pressed))
        if is_pressed is True:
            win.SetBorderColour(wx.RED)
        else:
            win.SetBorderColour(wx.WHITE)
