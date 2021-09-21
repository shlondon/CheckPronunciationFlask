# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.buttons.checkbutton.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A custom check/radio buttons with eventually a label text.

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

from ...tools import sppasSwissKnife
from ..image import ColorizeImage
from ..winevents import sb
from .basebutton import BaseCheckButton

# ---------------------------------------------------------------------------


class CheckButton(BaseCheckButton):
    """A custom checkable-button with a label text.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseCheckButton => CheckButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 label=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name=wx.ButtonNameStr):
        """Default class constructor.

        :param parent: the parent (required);
        :param id: window identifier.
        :param label: label text of the check button;
        :param pos: the position;
        :param size: the size;
        :param name: the name.

        """
        self._label = label
        self._radio = False
        # Set the spacing between the check bitmap and the label to 6.
        # This can be changed using SetSpacing later.
        self._spacing = 6

        super(CheckButton, self).__init__(parent, id, pos, size, name)

    # ------------------------------------------------------------------------

    def GetLabel(self):
        """Return the label text as it was passed to SetLabel."""
        return self._label

    # ------------------------------------------------------------------------

    def SetLabel(self, label):
        """Set the label text.

        :param label: (str) Label text.

        """
        self._label = label

    # ------------------------------------------------------------------------

    def IsChecked(self):
        """Return if button is checked.

        :returns: (bool)

        """
        return self._pressed

    # ------------------------------------------------------------------------

    def SetSpacing(self, spacing):
        """Set a new spacing between the check bitmap and the text.

        :param spacing: (int) Value between 0 and 30.

        """
        spacing = int(spacing)
        if spacing < 0:
            spacing = 0
        if spacing > 30:
            # wx.LogWarning('Spacing of a button is maximum 30px width. '
            #                'Got {:d}.'.format(spacing))
            spacing = 30
        # we should check if spacing < self height or width
        self._spacing = spacing

    # ------------------------------------------------------------------------

    def GetSpacing(self):
        """Return the spacing between the bitmap and the text."""
        return self._spacing

    # ------------------------------------------------------------------------

    def SetValue(self, value):
        """Set the state of the button.

        :param value: (bool)

        """
        self.Check(value)

    # ------------------------------------------------------------------------

    def GetValue(self):
        """Return the state of the button."""
        return self._pressed

    # ------------------------------------------------------------------------

    def DrawCheckImage(self, dc, gc):
        """Draw the check image.

        """
        x, y, w, h = self.GetContentRect()
        x += self._vert_border_width
        y += self._horiz_border_width
        w -= (2 * self._vert_border_width)
        h -= ((2 * self._horiz_border_width) + self._focus_width + 2)

        if self._label is None or len(self._label) == 0:
            prop_size = int(min(h * 0.7, 32))
            img_size = max(16, prop_size)
        else:
            tw, th = self.get_text_extend(dc, gc, "XX")
            img_size = int(float(th) * 1.2)

        box_x = 2
        box_y = (h - img_size) // 2

        # Adjust image size then draw
        if self._pressed:
            if self._radio:
                img = sppasSwissKnife.get_image('radio_checked')
            else:
                img = sppasSwissKnife.get_image('choice_checked')
        else:
            if self._radio:
                img = sppasSwissKnife.get_image('radio_unchecked')
            else:
                img = sppasSwissKnife.get_image('choice_checkbox')

        sppasSwissKnife.rescale_image(img, img_size)
        ColorizeImage(img, wx.BLACK, self.GetPenForegroundColour())

        # Draw image as bitmap
        bmp = wx.Bitmap(img)
        if wx.Platform == '__WXGTK__':
            dc.DrawBitmap(bmp, box_x, box_y)
        else:
            gc.DrawBitmap(bmp, box_x, box_y)

        return img_size

    # ------------------------------------------------------------------------

    def __DrawLabel(self, dc, gc, x):
        w, h = self.GetClientSize()
        tw, th = self.get_text_extend(dc, gc, self._label)
        y = ((h - th) // 2)
        font = self.GetFont()
        gc.SetFont(font)
        dc.SetFont(font)
        if wx.Platform == '__WXGTK__':
            dc.SetTextForeground(self.GetPenForegroundColour())
            dc.DrawText(self._label, x, y)
        else:
            gc.SetTextForeground(self.GetPenForegroundColour())
            gc.DrawText(self._label, x, y)

    # ------------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        img_size = self.DrawCheckImage(dc, gc)
        if self._label:
            self.__DrawLabel(dc, gc, img_size + self._spacing)

# ---------------------------------------------------------------------------


class RadioButton(CheckButton):
    """A custom checkable-button with a label text in radio mode.

    :Inheritance:
    wx.Window => sppasDCWindow => sppasImageDCWindow => sppasWindow =>
    BaseCheckButton => CheckButton => RadioButton

    :Emitted events:
    sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
    sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
    sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED
    wx.EVT_RADIOBUTTON

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
        :param name: the name.

        """
        super(RadioButton, self).__init__(parent, id, label, pos, size, name)
        self._radio = True

    # ------------------------------------------------------------------------

    def NotifyWxButtonEvent(self):
        evt = wx.PyCommandEvent(wx.EVT_RADIOBUTTON.typeId, self.GetId())
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanelCheckButton(wx.Panel):

    def __init__(self, parent):
        super(TestPanelCheckButton, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
            name="Test CheckButton")

        self.SetForegroundColour(wx.Colour(150, 160, 170))

        btn_check_xs = CheckButton(self, pos=(25, 10), size=(32, 32), name="yes")
        btn_check_xs.Check(True)
        btn_check_xs.Enable(False)
        btn_check_xs.Enable(True)

        btn_check_s = CheckButton(self, label="disabled", pos=(100, 10), size=(128, 64), name="yes")
        btn_check_s.Enable(False)

        btn_check_m = CheckButton(self, label='The text label', pos=(200, 10), size=(384, 128), name="yes")
        font = self.GetFont().MakeBold().Scale(1.4)
        btn_check_m.SetFont(font)
        btn_check_m.SetBorderWidth(2)

        # ----
        # In order to replace the wx.EVT_CHECKBUTTON:
        btn_check_m.Bind(sb.EVT_WINDOW_SELECTED, self._on_selected)
        self.Bind(sb.EVT_WINDOW_FOCUSED, self._on_focused)
        self.Bind(sb.EVT_BUTTON_PRESSED, self._on_pressed)
        self.Bind(wx.EVT_CHECKBOX, self._on_check)

    # -----------------------------------------------------------------------

    def _on_check(self, event):
        win = event.GetEventObject()
        logging.debug("Button with name {:s} is checked.".format(win.GetName()))

    # -----------------------------------------------------------------------

    def _on_pressed(self, event):
        win = event.GetEventObject()
        is_pressed = event.GetPressed()
        logging.debug("CheckButton with name {:s} is pressed: {}".format(win.GetName(), is_pressed))
        if is_pressed is True:
            win.SetBorderColour(wx.RED)
        else:
            win.SetBorderColour(wx.WHITE)

    # -----------------------------------------------------------------------

    def _on_selected(self, event):
        obj = event.GetEventObject()
        is_selected = event.GetSelected()
        logging.debug("Button with name {:s} is selected: {}".format(obj.GetName(), is_selected))
        if is_selected is True:
            i = random.randint(1000, 9999)
            new_label = "Text-%d" % i
            obj.SetLabel(new_label)
            obj.Refresh()

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

    def SetForegroundColour(self, colour):
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)

# ----------------------------------------------------------------------------


class TestPanelRadioButton(wx.Panel):

    def __init__(self, parent):
        super(TestPanelRadioButton, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE,
            name="Test RadioButton")

        self.SetForegroundColour(wx.Colour(150, 160, 170))

        btn_check_xs = RadioButton(self, pos=(25, 10), size=(32, 32), name="yes")
        btn_check_xs.Check(True)

        btn_check_s = RadioButton(self, label="disabled", pos=(100, 10), size=(128, 64), name="dis")
        btn_check_s.Enable(False)

        btn_check_m = RadioButton(self, label='The text label', pos=(200, 10), size=(384, 128), name="radio")
        font = self.GetFont().MakeBold().Scale(1.4)
        btn_check_m.SetFont(font)
        btn_check_m.SetBorderWidth(8)

        # ----
        # In order to replace the wx.EVT_CHECKBUTTON:
        self.Bind(sb.EVT_WINDOW_SELECTED, self._on_selected)
        self.Bind(sb.EVT_WINDOW_FOCUSED, self._on_focused)
        self.Bind(sb.EVT_BUTTON_PRESSED, self._on_pressed)

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

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            c.SetForegroundColour(colour)
