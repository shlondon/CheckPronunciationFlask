# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.buttons.togglebutton.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A custom toggle button with eventually a bitmap/a label text.

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
import logging

from ..basewindow import WindowState
from ..winevents import sb
from ..winevents import sppasButtonPressedEvent
from .bitmapbutton import BitmapTextButton
from .textbutton import TextButton

# ---------------------------------------------------------------------------


class ToggleTextButton(TextButton):
    """A toggle button with a label text only.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseButton => TextButton => ToggleTextButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED
    wx.EVT_TOGGLEBUTTON

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor."""
        self._pressed = False

        super(ToggleTextButton, self).__init__(
            parent, id, label=label, pos=pos, size=size, name=name)

    # -----------------------------------------------------------------------

    def IsPressed(self):
        """Return if button is pressed.

        :returns: (bool)

        """
        return self._pressed

    # -----------------------------------------------------------------------

    def GetValue(self):
        """Return the pressed value."""
        return self._pressed

    # -----------------------------------------------------------------------

    def SetValue(self, value):
        """Set the pressed value.

        :param value: (bool)

        """
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
            if self._state[1] == WindowState().focused:
                self.NotifyFocused(value=True)

            evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
            evt.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(evt)

    # -----------------------------------------------------------------------

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

# ---------------------------------------------------------------------------


class ToggleButton(BitmapTextButton):
    """A toggle button with a label text and a bitmap.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseButton => TextButton => BitmapTextButton => ToggleTextButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED
    wx.EVT_TOGGLEBUTTON

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor."""
        self._pressed = False

        super(ToggleButton, self).__init__(
            parent, id, label=label, pos=pos, size=size, name=name)

    # -----------------------------------------------------------------------

    def IsPressed(self):
        """Return if button is pressed.

        :returns: (bool)

        """
        return self._pressed

    # -----------------------------------------------------------------------

    def GetValue(self):
        """Return the pressed value."""
        return self._pressed

    # -----------------------------------------------------------------------

    def SetValue(self, value):
        """Set the pressed value.

        :param value: (bool)

        """
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
            if self._state[1] == WindowState().focused:
                self.NotifyFocused(value=True)

            evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.GetId())
            evt.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(evt)

    # -----------------------------------------------------------------------

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

# ---------------------------------------------------------------------------


class TestPanelToggleButton(wx.Panel):

    def __init__(self, parent):
        super(TestPanelToggleButton, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
            name="Test ToggleButton")

        self.SetForegroundColour(wx.Colour(150, 160, 170))
        # b1 = BitmapTextButton(self, label="sppas_colored")
        # b2 = BitmapTextButton(self, name="like")

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(ToggleButton(self), 1, wx.EXPAND, 0)
        sizer.Add(ToggleButton(self, name="rotate_screen"), 1, wx.EXPAND, 0)
        sizer.Add(ToggleTextButton(self, label=""), 1, wx.EXPAND, 0)
        sizer.Add(ToggleTextButton(self, label="label"), 1, wx.EXPAND, 0)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        # ----
        # In order to replace the wx.EVT_BUTTON:
        self.Bind(sb.EVT_WINDOW_SELECTED, self._on_selected)
        self.Bind(sb.EVT_WINDOW_FOCUSED, self._on_focused)
        self.Bind(sb.EVT_BUTTON_PRESSED, self._on_pressed)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)

    # -----------------------------------------------------------------------

    def _on_pressed(self, event):
        win = event.GetEventObject()
        is_pressed = event.GetPressed()
        logging.debug("Button with name {:s} is pressed: {}".format(win.GetName(), is_pressed))

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
