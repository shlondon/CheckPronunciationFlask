# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.buttonbox.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A buttonbox with our custom buttons.

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

import logging
import wx

from .winevents import sb
from .buttons import RadioButton
from .buttons import CheckButton
from .buttons import ToggleButton
from .panels import sppasPanel
from .panels import sppasScrolledPanel

# ---------------------------------------------------------------------------


class sppasRadioBoxPanel(sppasScrolledPanel):
    """A radio box is a list of mutually exclusive radio buttons.

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 choices=(),
                 majorDimension=0,
                 style=wx.RA_SPECIFY_COLS,
                 name=wx.RadioBoxNameStr):
        super(sppasRadioBoxPanel, self).__init__(parent, id, pos, size, name=name)

        self._buttons = list()
        self._selection = -1
        gap = sppasPanel.fix_size(2)
        self._major_dimension = majorDimension
        self._style = style
        self._create_content(choices, gap, gap)
        self._setup_events()

        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.Layout()

    # ------------------------------------------------------------------------

    def DoGetBestSize(self):
        if self.GetSizer() is None or len(self._buttons) == 0:
            # min enough values to provide warnings due to the scrollbars
            size = wx.Size(sppasPanel.fix_size(10), sppasPanel.fix_size(20))
        else:
            c = self.GetSizer().GetCols()
            r = self.GetSizer().GetRows()
            min_width = self.get_font_height()
            for b in self._buttons:
                mw, mh = b.GetMinSize()
                if mw > min_width:
                    min_width = mw

            min_width = (min_width * c) + ((sppasPanel.fix_size(2) + self.GetSizer().GetVGap()) * (c+1))
            expected_height = (r * int(float(self.get_font_height() * 1.8))) + \
                              (r * (sppasPanel.fix_size(2) + self.GetSizer().GetHGap()))
            if c == 1:
                min_height = min(expected_height,
                                 sppasPanel.fix_size(100))  # SHOULD BE DYNAMICALLY ESTIMATED
            else:
                min_height = expected_height

            size = wx.Size(min_width, min_height)

        return size

    # ------------------------------------------------------------------------

    def EnableItem(self, n, enable=True):
        """Enable or disable an individual button in the radiobox.

        :param n: (int) The zero-based button to enable or disable.
        :param enable: (bool) True to enable, False to disable.
        :returns: (bool)

        """
        if n < 0:
            return False
        if n > len(self._buttons):
            return False
        # do not disable the selected button
        if n == self._selection and enable is False:
            return False

        self._buttons[n].Enable(enable)
        return True

    # ------------------------------------------------------------------------

    def FindString(self, string, bCase=False):
        """Find a button matching the given string.

        :param string: (string) – The string to find.
        :param bCase: (bool) – Should the search be case-sensitive?

        :returns: (int) the position if found, or -1 if not found.

        """
        found = -1
        for i, c in enumerate(self._buttons):
            label = c.GetLabel()
            if bCase is False and label.lower() == string.lower():
                found = i
                break
            if bCase is True and label == string:
                found = i
                break
        return found

    # ------------------------------------------------------------------------

    def GetColumnCount(self):
        """Return the number of columns in the radiobox."""
        return self.GetSizer().GetEffectiveColsCount()

    # ------------------------------------------------------------------------

    def GetRowCount(self):
        """Return the number of rows in the radiobox."""
        return self.GetSizer().GetEffectiverowsCount()

    # ------------------------------------------------------------------------

    def GetCount(self):
        """Return the number of items in the control."""
        return len(self._buttons)

    # ------------------------------------------------------------------------

    def GetSelection(self):
        """Return the index of the selected item or -1 if no item is selected.
    
        :returns: (int) The position of the current selection.
        
        """
        return self._selection

    # ------------------------------------------------------------------------

    def SetSelection(self, n):
        """Set the selection to the given item.

        :param n: (int) – Index of the item or -1 to disable the current

        """
        if n > len(self._buttons):
            return

        if n >= 0:
            btn = self._buttons[n]
            # do not select a disabled button
            if btn.IsEnabled() is True:
                # un-select the current selected button
                if self._selection not in (-1, n):
                    self._activate(self._selection, False)
                # select the expected one
                self._selection = n
                self._activate(n, True)
                btn.SetValue(True)
        else:
            # un-select the current selected button
            if self._selection != -1:
                self._activate(self._selection, False)
            self._selection = -1

    # ------------------------------------------------------------------------

    def GetString(self, n):
        """Return the label of the item with the given index.

        :param n: (int) – The zero-based index.
        :returns: (str) The label of the item or an empty string if the position
        was invalid.

        """
        if n < 0:
            return ""
        if n > len(self._buttons):
            return ""
        return self._buttons[n].GetLabel()

    # ------------------------------------------------------------------------

    def GetStringSelection(self):
        """Return the label of the selected item.

        :returns: (str) The label of the selected item

        """
        if self._selection >= 0:
            return self._buttons[self._selection].GetLabel()
        return ""

    # ------------------------------------------------------------------------

    def GetItemLabel(self, n):
        """Return the text of the n'th item in the radio box.

        :param n: (int) – The zero-based index.

        """
        self.GetString(n)

    # ------------------------------------------------------------------------

    def IsItemEnabled(self, n):
        """Return True if the item is enabled or False if it was disabled using Enable.

        :param n: (int) – The zero-based index.
        :returns: (bool)

        """
        if n < 0:
            return False
        if n > len(self._buttons):
            return False
        return self._buttons[n].IsEnabled()

    # ------------------------------------------------------------------------

    def SetItemLabel(self, n, text):
        """Set the text of the n'th item in the radio box.

        :param n: (int) The zero-based index.

        """
        if n < 0:
            return False
        if n > len(self._buttons):
            return False
        self._buttons[n].SetLabel(text)
        self._buttons[n].Refresh()
        return True

    # ------------------------------------------------------------------------

    def SetString(self, n, string):
        """Set the label for the given item.

        :param n: (int) The zero-based item index.
        :param string: (string) The label to set.

        """
        return self.SetItemLabel(n, string)

    # ------------------------------------------------------------------------

    def ShowItem(self, item, show=True):
        """Show or hide individual buttons.

        :param item: (int) The zero-based position of the button to show or hide.
        :param show: (bool) True to show, False to hide.
        :return: (bool) True if the item has been shown or hidden or False
        if nothing was done because it already was in the requested state.

        """
        if item > len(self._buttons) or item < 0:
            return False
        btn = self._buttons[item]
        self.GetSizer().Show(btn, show)
        self.GetSizer().Layout()
        return True

    # ------------------------------------------------------------------------

    def IsItemShown(self, n):
        """Return True if the item is currently shown or False if it was hidden using Show.

        :param n: (int) The zero-based item index.
        :returns: (bool)

        """
        if n > len(self._buttons) or n < 0:
            return False
        return self._buttons[n].IsShown()

    # ------------------------------------------------------------------------

    def GetItems(self):
        """Return the list of choices (list of str)."""
        return [btn.GetLabel() for btn in self._buttons]

    # ------------------------------------------------------------------------

    def SetVGap(self, value):
        self.GetSizer().SetVGap(value)

    # ------------------------------------------------------------------------

    def SetHGap(self, value):
        self.GetSizer().SetHGap(value)

    # ------------------------------------------------------------------------

    def Append(self, string):
        choices = self.GetItems()
        enabled = list()
        showed = list()
        for btn in self._buttons:
            enabled.append(btn.IsEnabled())
            showed.append(btn.IsShown())
        self.GetSizer().Clear(delete_windows=True)
        self._buttons = list()

        choices.append(string)
        enabled.append(True)
        showed.append(True)

        rows, cols = self.get_rows_cols_counts(choices)
        logging.debug(" append. choices {} . nb estimated rows = {}".format(choices, rows))

        self._append_choices_to_sizer(choices, rows, cols)

        for i, btn in enumerate(self._buttons):
            btn.Enable(enabled[i])
            self.ShowItem(i, show=showed[i])

        self.SetSelection(self._selection)
        self.SetSize(self.DoGetBestSize())
        self.Layout()

        return len(self._buttons) - 1

    # ------------------------------------------------------------------------

    def Delete(self, n):
        """Delete the n-th entry.

        Actually, destroy all buttons and re-create only the relevant ones.

        """
        choices = self.GetItems()
        choices.pop(n)
        self._buttons.pop(n)
        enabled = list()
        showed = list()
        if self._selection == n:
            self._selection = -1
        elif self._selection > n:
            self._selection -= 1
        for btn in self._buttons:
            enabled.append(btn.IsEnabled())
            showed.append(btn.IsShown())
        self.GetSizer().Clear(delete_windows=True)
        self._buttons = list()

        rows, cols = self.get_rows_cols_counts(choices)
        self._append_choices_to_sizer(choices, rows, cols)

        for i, btn in enumerate(self._buttons):
            btn.Enable(enabled[i])
            self.ShowItem(i, show=showed[i])

        self.SetSelection(self._selection)
        self.SetSize(self.DoGetBestSize())
        self.Layout()

    # ------------------------------------------------------------------------

    def DeleteAll(self):
        for btn in self._buttons:
            btn.Destroy()
        self._buttons = list()
        self._selection = -1
        self.SetSize(self.DoGetBestSize())
        self.Layout()

    # ------------------------------------------------------------------------

    def get_rows_cols_counts(self, choices):
        """Return the number of rows and cols."""
        rows = 1
        cols = 1
        if len(choices) > 1:
            if self._major_dimension > 1:
                if self._style == wx.RA_SPECIFY_COLS:
                    cols = self._major_dimension
                    rows = (len(choices)+1) // self._major_dimension
                elif self._style == wx.RA_SPECIFY_ROWS:
                    logging.debug("NB rows fixed to {:d}; choices={}".format(self._major_dimension, choices))
                    rows = self._major_dimension
                    cols = len(choices) // self._major_dimension
                    if len(choices) % self._major_dimension > 0:
                        cols += 1
                    logging.debug("nb cols = {}".format(cols))

            else:  # one dimension
                if self._style == wx.RA_SPECIFY_COLS:
                    cols = 1
                    rows = len(choices)
                elif self._style == wx.RA_SPECIFY_ROWS:
                    rows = 1
                    cols = len(choices)
        return rows, cols

    # ------------------------------------------------------------------------
    # Private methods to construct the panel.
    # ------------------------------------------------------------------------

    def _create_content(self, choices, hgap=0, vgap=0):
        """Create the main content."""
        rows, cols = self.get_rows_cols_counts(choices)
        grid = wx.GridBagSizer(vgap=vgap, hgap=hgap)
        grid.SetFlexibleDirection(wx.BOTH)
        self.SetSizer(grid)

        self._append_choices_to_sizer(choices, rows, cols)
        if len(choices) > 0:
            try:
                self.SetSelection(0)
            except:
                pass

    # -----------------------------------------------------------------------

    def _append_choices_to_sizer(self, choices, rows, cols):
        grid = self.GetSizer()

        if self._style == wx.RA_SPECIFY_COLS:
            for c in range(cols):
                for r in range(rows):
                    index = (c*rows)+r
                    if index < len(choices):
                        btn = self._create_button(label=choices[index],
                                                  name="button_%d_%d" % (c, r))
                        grid.Add(btn, pos=(r, c), flag=wx.EXPAND | wx.LEFT | wx.TOP, border=sppasPanel.fix_size(2))
                        self._buttons.append(btn)

        else:
            for r in range(rows):
                for c in range(cols):
                    index = (r*cols)+c
                    if index < len(choices):
                        btn = self._create_button(label=choices[index],
                                                  name="button_%d_%d" % (r, c))
                        grid.Add(btn, pos=(r, c), flag=wx.EXPAND | wx.LEFT | wx.TOP, border=sppasPanel.fix_size(2))
                        self._buttons.append(btn)

        for c in range(cols):
            if grid.IsColGrowable(c) is False:
                grid.AddGrowableCol(c)
        for r in range(rows):
            if grid.IsRowGrowable(r):
                grid.AddGrowableRow(r)

    # -----------------------------------------------------------------------

    def _create_button(self, label, name):
        """Create the button to add into the box."""
        btn = RadioButton(self, label=label, name=name)
        btn.Enable(True)
        btn.SetValue(False)
        # estimate min size:
        w = self.get_font_width()
        mw = w * len(label)
        btn.SetMinSize(wx.Size(mw, int(float(self.get_font_height()) * 1.8)))
        #btn.SetSize(wx.Size(mw, int(float(self.get_font_height()) * 1.8)))
        return btn

    # ------------------------------------------------------------------------

    def _activate(self, n, value):
        """Check/Uncheck the n-th button."""
        btn = self._buttons[n]
        if btn.IsEnabled() is True:
            btn.SetValue(value)

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # The user pressed a key of its keyboard
        # self.Bind(wx.EVT_KEY_DOWN, self._process_key_event)

        # Emitted events by the radio buttons:
        #    - sppasWindowSelectedEvent - bind with sb.EVT_WINDOW_SELECTED
        #    - sppasWindowFocusedEvent - bind with sb.EVT_WINDOW_FOCUSED
        #    - sppasButtonPressedEvent - bind with sb.EVT_BUTTON_PRESSED
        self.Bind(sb.EVT_BUTTON_PRESSED, self._process_btn_event)

    # ------------------------------------------------------------------------

    def _process_btn_event(self, event):
        """Respond to a button event.

        :param event: (wx.Event)

        """
        evt_btn = event.GetEventObject()
        new_selected_index = self._buttons.index(evt_btn)
        self.SetSelection(new_selected_index)
        self.Notify()

    # ------------------------------------------------------------------------

    def Notify(self):
        """Sends a wx.EVT_RADIOBOX event to the listener (if any)."""
        evt = wx.PyCommandEvent(wx.EVT_RADIOBOX.typeId, self.GetId())
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)

# ----------------------------------------------------------------------------


class sppasCheckBoxPanel(sppasRadioBoxPanel):
    """A check box is a list of check buttons.

    The parent can bind wx.EVT_CHECKBOX.

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 choices=[],
                 majorDimension=0,
                 style=wx.RA_SPECIFY_COLS,
                 name=wx.RadioBoxNameStr):
        super(sppasCheckBoxPanel, self).__init__(parent, id, pos, size, choices, majorDimension, style, name)
        self._selection = list()
        for i in range(len(self._buttons)):
            self._buttons[i].SetValue(False)

    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        pass

    # -----------------------------------------------------------------------

    def _create_button(self, label, name):
        """Create the button to add into the box."""
        btn = CheckButton(self, label=label, name=name)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(h//4)
        btn.SetSpacing(sppasPanel.fix_size(h))

        btn.Enable(True)
        btn.SetValue(False)

        btn.SetMinSize(wx.Size(-1, int(float(self.get_font_height()) * 1.8)))
        #btn.SetSize(wx.Size(-1, int(float(self.get_font_height()) * 1.8)))
        btn.Bind(sb.EVT_BUTTON_PRESSED, self._process_btn_event)
        btn.Bind(wx.EVT_CHECKBOX, self._process_checked_event)

        return btn
    # ------------------------------------------------------------------------

    def _process_checked_event(self, event):
        # Capture the event in order to not propagate it.
        pass

    # ------------------------------------------------------------------------

    def EnableItem(self, n, enable=True):
        """Enable or disable an individual button in the box.

        :param n: (int) The zero-based button to enable or disable.
        :param enable: (bool) True to enable, False to disable.
        :returns: (bool)

        """
        if n < 0:
            return False
        if n > len(self._buttons):
            return False

        self._buttons[n].Enable(enable)
        return True

    # ------------------------------------------------------------------------

    def SetSelection(self, n, value=True):
        """Set the given item selected.

        :param n: (int) – Index of the item to select
        :param value: (bool) – Select or un-select the given item

        """
        if n > len(self._buttons):
            return

        if n >= 0:
            btn = self._buttons[n]
            # do not select a disabled button
            if btn.IsEnabled() is True:
                # select the expected item and add to selection or the contrary
                self._activate(n, value)

    # ------------------------------------------------------------------------

    def GetSelection(self):
        """Return the list of indexes of the selected items.

        :returns: (list of int)

        """
        if len(self._selection) > 0:
            return tuple(self._selection)
        return list()

    # ------------------------------------------------------------------------

    def GetStringSelection(self):
        """Return the list of labels of the selected items.

        :returns: (list of str) The labels of the selected items

        """
        if len(self._selection) > 0:
            return [self._buttons[i].GetLabel() for i in range(len(self._buttons)) if i in self._selection]
        return list()

    # ------------------------------------------------------------------------

    def Notify(self):
        """Override."""
        evt = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId, self.GetId())
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)

    # ------------------------------------------------------------------------

    def _process_btn_event(self, event):
        """Respond to a button event.

        :param event: (wx.Event)

        """
        evt_btn = event.GetEventObject()
        new_clicked_index = self._buttons.index(evt_btn)
        self._activate(new_clicked_index, evt_btn.GetValue())
        self.Notify()

    # ------------------------------------------------------------------------

    def Append(self, string):
        choices = self.GetItems()
        enabled = list()
        showed = list()
        selected = list()

        for btn in self._buttons:
            enabled.append(btn.IsEnabled())
            showed.append(btn.IsShown())
            selected.append(btn.GetValue())
        self.GetSizer().Clear(delete_windows=True)
        self._buttons = list()
        self._selection = list()

        choices.append(string)
        enabled.append(True)
        showed.append(True)
        selected.append(False)

        rows, cols = self.get_rows_cols_counts(choices)
        self._append_choices_to_sizer(choices, rows, cols)

        for i, btn in enumerate(self._buttons):
            btn.Enable(enabled[i])
            self.ShowItem(i, show=showed[i])
            self._activate(i, selected[i])

        self.SetMinSize(self.DoGetBestSize())
        self.Layout()

        return len(self._buttons) - 1

    # ------------------------------------------------------------------------

    def Delete(self, n):
        """Delete the n-th entry.

        Actually, destroy all buttons and re-create only the relevant ones.

        """
        choices = self.GetItems()
        choices.pop(n)
        self._buttons.pop(n)
        enabled = list()
        showed = list()
        selected = list()
        if n in self._selection:
            self._selection.remove(n)

        for btn in self._buttons:
            enabled.append(btn.IsEnabled())
            showed.append(btn.IsShown())
            selected.append(btn.GetValue())
        self.GetSizer().Clear(delete_windows=True)
        self._buttons = list()
        self._selection = list()

        rows, cols = self.get_rows_cols_counts(choices)
        self._append_choices_to_sizer(choices, rows, cols)

        for i, btn in enumerate(self._buttons):
            btn.Enable(enabled[i])
            self.ShowItem(i, show=showed[i])
            self._activate(i, selected[i])

        self.SetMinSize(self.DoGetBestSize())
        self.Layout()

    # ------------------------------------------------------------------------

    def DeleteAll(self):
        for btn in self._buttons:
            btn.Destroy()
        self._buttons = list()
        self._selection = list()
        self.SetSize(self.DoGetBestSize())
        self.Layout()

    # ------------------------------------------------------------------------

    def _activate(self, n, value):
        """Check/Uncheck the n-th button."""
        btn = self._buttons[n]
        if btn.IsEnabled() is True:
            btn.SetValue(value)
            if value is True and n not in self._selection:
                self._selection.append(n)
            if value is False and n in self._selection:
                self._selection.remove(n)

# ----------------------------------------------------------------------------


class sppasToggleBoxPanel(sppasRadioBoxPanel):
    """A toggle box is a list of mutually exclusive toggle buttons.

    The parent can bind wx.EVT_RADIOBOX.

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 choices=[],
                 majorDimension=0,
                 style=wx.RA_SPECIFY_COLS,
                 name=wx.RadioBoxNameStr):
        super(sppasToggleBoxPanel, self).__init__(parent, id, pos, size, choices, majorDimension, style, name)

    # -----------------------------------------------------------------------

    def _create_button(self, label, name):
        """Create the button to add into the box."""
        btn = ToggleButton(self, label=label, name=name)
        btn.SetImage(None)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetLabelPosition(wx.LEFT)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(h//4)
        btn.SetSpacing(sppasPanel.fix_size(h))
        btn.SetAlign(wx.ALIGN_LEFT)

        btn.Enable(True)
        btn.SetValue(False)

        # estimate min size:
        mw = h * (len(label) + 2)
        btn.SetMinSize(wx.Size(mw, int(float(self.get_font_height()) * 1.8)))
        btn.SetSize(wx.Size(mw, int(float(self.get_font_height()) * 1.8)))

        return btn

    # ------------------------------------------------------------------------

    def _activate(self, n, value):
        """Check/Uncheck the n-th button."""
        btn = self._buttons[n]
        if btn.IsEnabled() is True:
            btn.SetValue(value)
            if value is True:
                btn.SetImage("check_yes")
            else:
                btn.SetImage(None)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanelRadioBox(wx.Panel):

    def __init__(self, parent):
        super(TestPanelRadioBox, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test RadioBox")

        rbc = sppasRadioBoxPanel(
            self,
            pos=(10, 10),
            size=wx.Size(200, 300),
            choices=["bananas", "pears", "tomatoes", "apples", "pineapples"],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            name="radio_in_cols")
        rbc.Bind(wx.EVT_RADIOBOX, self.on_btn_event)
        # disable apples:
        rbc.EnableItem(3, False)
        rbc.SetBackgroundColour(wx.RED)
        rbc.SetSelection(1)
        rbc.EnableItem(1, False)
        rbc.EnableItem(1, True)
        # should do return False:
        # assert(rbc.EnableItem(50, True) is False), "Enable Item with index 50:"

        rbr = sppasRadioBoxPanel(
            self,
            pos=(220, 10),
            size=wx.Size(300, 200),
            choices=["fruits de la passion", "jujube", "bananes", "pommes", "ananas"],
            majorDimension=2,
            style=wx.RA_SPECIFY_ROWS,
            name="radio_in_rows")
        rbr.Bind(wx.EVT_RADIOBOX, self.on_btn_event)
        # disable pommes
        rbr.EnableItem(3, False)
        rbc.SetBackgroundColour(wx.BLUE)

        tbc = sppasToggleBoxPanel(
            self, pos=(550, 10), size=wx.Size(200, 200),
            choices=["choix 1", "choix 2", "choix 3", "choix 3--", "choix 4", "choix 5", "choix 6"],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
            name="toogle_in_cols"
        )
        tbc.SetVGap(0)
        tbc.SetHGap(0)
        tbc.EnableItem(3, False)
        tbc.Append("Append 1")
        tbc.Delete(2)
        tbc.Append("Append 2")
        tbc.SetItemLabel(1, "changed 2")
        tbc.Refresh()
        tbc.Bind(wx.EVT_RADIOBOX, self.on_btn_event)
        rbc.SetBackgroundColour(wx.LIGHT_GREY)

        cbc = sppasCheckBoxPanel(
            self, pos=(500, 250), size=wx.Size(200, 200),
            choices=["check 1", "check 2"],
            majorDimension=2,
            style=wx.RA_SPECIFY_COLS,
            name="check_in_cols"
        )
        cbc.SetVGap(2)
        cbc.SetHGap(2)
        cbc.Append("Appended 1")
        cbc.Append("Appended 2")
        cbc.Append("Appended 3")
        cbc.Append("Appended 4")
        cbc.Append("Appended 5")
        cbc.SetBackgroundColour(wx.YELLOW)
        cbc.SetSelection(0)
        cbc.EnableItem(0, False)
        cbc.SetSelection(1)
        cbc.EnableItem(1, False)
        cbc.EnableItem(1, True)
        cbc.EnableItem(2, False)
        #cbc.Layout()
        cbc.Refresh()
        cbc.Bind(wx.EVT_CHECKBOX, self.on_btn_check_event)

        tbr = sppasToggleBoxPanel(
            self, pos=(10, 400), size=wx.Size(400, 100),
            choices=["choice 1", "choice 2", "choice 3", "choice 4", "choice 5"],
            majorDimension=3,
            style=wx.RA_SPECIFY_ROWS,
            name="toogle_in_rows"
        )
        tbr.SetBackgroundColour(wx.YELLOW)
        tbr.Append("ajout 1")
        tbr.Append("ééééé 2")
        tbr.EnableItem(2, False)
        #tbr.Layout()
        tbr.Refresh()
        tbr.Bind(wx.EVT_RADIOBOX, self.on_btn_event)

    # -----------------------------------------------------------------------

    def on_btn_event(self, event):
        obj = event.GetEventObject()
        logging.debug('* * * RadioBox Event by {:s} * * *'.format(obj.GetName()))
        logging.debug(" --> selection index: {:d}".format(obj.GetSelection()))
        logging.debug(" --> selection label: {:s}".format(obj.GetStringSelection()))

    def on_btn_check_event(self, event):
        obj = event.GetEventObject()
        logging.debug('* * * CheckBox Event by {:s} * * *'.format(obj.GetName()))
        logging.debug(" --> selection indexes: {}".format(obj.GetSelection()))
        logging.debug(" --> selection labels: {}".format(obj.GetStringSelection()))
