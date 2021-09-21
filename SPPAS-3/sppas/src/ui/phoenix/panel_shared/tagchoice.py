# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.panel_shared.tagchoice.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Panels to fix filter ctriteria on tags.

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

from sppas.src.config import msg
from sppas.src.utils import u

from sppas.src.ui.phoenix.windows import sb
from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.text import sppasStaticText
from sppas.src.ui.phoenix.windows.text import sppasTextCtrl
from sppas.src.ui.phoenix.windows import sppasRadioBoxPanel
from sppas.src.ui.phoenix.windows.buttons import CheckButton
from sppas.src.ui.phoenix.windows.buttons import BitmapButton

# --------------------------------------------------------------------------


def _(message):
    return u(msg(message, "ui"))


MSG_TAG_TYPE_BOOL = _("Boolean value of the tag is:")
MSG_TAG_TYPE_INT = _("Integer value of the tag is:")
MSG_TAG_TYPE_FLOAT = _("Float value of the tag is:")
MSG_TAG_TYPE_STR_2 = _("Patterns to find, separated by commas:")
MSG_TAG_TYPE_STR_1 = _("Pattern:")
DEFAULT_LABEL = "tag1, tag2, ..."
MSG_CASE = _("Case sensitive")

MSG_FALSE = _("False")
MSG_TRUE = _("True")

MSG_EQUAL = _("equal to")
MSG_NOT_EQUAL = _("not equal to")
MSG_GT = _("greater than")
MSG_LT = _("less than")
MSG_GE = _("greater or equal to")
MSG_LE = _("less or equal to")

MSG_EXACT = _("exact")
MSG_CONTAINS = _("contains")
MSG_STARTSWITH = _("starts with")
MSG_ENDSWITH = _("ends with")
MSG_REGEXP = _("match (regexp)")
MSG_NOT_EXACT = _("not exact")
MSG_NOT_CONTAINS = _("not contains")
MSG_NOT_STARTSWITH = _("not starts with")
MSG_NOT_ENDSWITH = _("not ends with")
MSG_NOT_REGEXP = _("not match (regexp)")
MSG_FROM = _("starting at")
MSG_TO = _("ending at")
MSG_VALUE = _("this value:")

# ---------------------------------------------------------------------------


class sppasTagStringsPanel(sppasPanel):
    """Panel to get a filter on a sppasTag if its type is 'str'.

    """

    choices = (
               (MSG_EXACT, "exact"),
               (MSG_CONTAINS, "contains"),
               (MSG_STARTSWITH, "startswith"),
               (MSG_ENDSWITH, "endswith"),
               (MSG_REGEXP, "regexp"),

               (MSG_NOT_EXACT, "exact"),
               (MSG_NOT_CONTAINS, "contains"),
               (MSG_NOT_STARTSWITH, "startswith"),
               (MSG_NOT_ENDSWITH, "endswith"),
               (MSG_NOT_REGEXP, "regexp"),
              )

    def __init__(self, parent):
        super(sppasTagStringsPanel, self).__init__(parent)
        top_label = sppasStaticText(self, label=MSG_TAG_TYPE_STR_2)
        top_label.SetMinSize(wx.Size(sppasPanel.fix_size(320), -1))
        self.text = sppasTextCtrl(self, value=DEFAULT_LABEL)

        functions = [row[0] for row in sppasTagStringPanel.choices]
        self.radiobox = sppasRadioBoxPanel(
            self,
            choices=functions,
            majorDimension=2,
            style=wx.RA_SPECIFY_COLS)
        self.radiobox.SetSelection(1)

        self.checkbox = CheckButton(self, label=MSG_CASE)
        self.checkbox.SetMinSize(wx.Size(-1, self.get_font_height()*2))
        self.checkbox.SetFocusWidth(0)
        self.checkbox.SetValue(True)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        b = sppasPanel.fix_size(6)
        sizer.Add(top_label, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.text, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.radiobox, 0, flag=wx.EXPAND | wx.ALL,border=b*2)
        sizer.Add(self.checkbox, 0, flag=wx.EXPAND | wx.ALL, border=b)

        self.SetSizerAndFit(sizer)

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): one of the methods in Compare
               - values (list): patterns to find

        """
        idx = self.radiobox.GetSelection()
        label = self.radiobox.GetStringSelection()
        given_fct = sppasTagStringPanel.choices[idx][1]

        # Fill the resulting dict
        prepend_fct = ""

        if given_fct != "regexp":
            # prepend "not_" if reverse
            if "not" in label:
                prepend_fct += "not_"
            # prepend "i" if case-insensitive
            if self.checkbox.GetValue() is False:
                prepend_fct += "i"

            # fix the value to find (one or several with the same function)
            given_patterns = self.text.GetValue()
            values = given_patterns.split(',')
            values = [" ".join(p.split()) for p in values]
        else:
            values = [self.text.GetValue()]

        return "tag", prepend_fct+given_fct, values

# ---------------------------------------------------------------------------


class sppasTagStringPanel(sppasPanel):
    """Panel to get a filter on a sppasTag if its type is 'str'.

    """

    choices = (
               (MSG_EXACT, "exact"),
               (MSG_CONTAINS, "contains"),
               (MSG_STARTSWITH, "startswith"),
               (MSG_ENDSWITH, "endswith"),
               (MSG_REGEXP, "regexp"),

               (MSG_NOT_EXACT, "exact"),
               (MSG_NOT_CONTAINS, "contains"),
               (MSG_NOT_STARTSWITH, "startswith"),
               (MSG_NOT_ENDSWITH, "endswith"),
               (MSG_NOT_REGEXP, "regexp"),
              )

    def __init__(self, parent):
        super(sppasTagStringPanel, self).__init__(parent)
        h = self.get_font_height()

        # A line with "Pattern: TEXT ENTRY [broom]"
        p = sppasPanel(self)
        s = wx.BoxSizer(wx.HORIZONTAL)
        pattern = sppasStaticText(p, label=MSG_TAG_TYPE_STR_1)
        entry = sppasTextCtrl(p, value="", name="text_entry")
        entry.SetMinSize(wx.Size(sppasPanel.fix_size(256), h*2))
        broom = BitmapButton(p, name="broom")
        broom.SetFocusWidth(0)
        broom.SetMinSize(wx.Size(h * 2, -1))
        broom.Bind(sb.EVT_WINDOW_SELECTED, self._on_broom)
        s.Add(pattern, 0, wx.LEFT | wx.EXPAND, sppasPanel.fix_size(2))
        s.Add(entry, 1, wx.LEFT | wx.EXPAND, sppasPanel.fix_size(2))
        s.Add(broom, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, sppasPanel.fix_size(2))
        p.SetSizer(s)

        # The functions the pattern can match
        functions = [row[0] for row in sppasTagStringPanel.choices]
        radiobox = sppasRadioBoxPanel(self, choices=functions, majorDimension=2, style=wx.RA_SPECIFY_COLS)
        radiobox.SetSelection(1)
        radiobox.SetName("radio_functions")
        radiobox.SetMinSize(wx.Size(-1, (len(functions)+1)*h))

        # Option for searching: case sensitive
        checkbox = CheckButton(self, label=MSG_CASE, name="check_case")
        checkbox.SetMinSize(wx.Size(-1, self.get_font_height()*2))
        checkbox.SetFocusWidth(0)
        checkbox.SetValue(True)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        b = sppasPanel.fix_size(6)
        sizer.Add(p, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(radiobox, 0, flag=wx.EXPAND | wx.ALL, border=b*2)
        sizer.Add(checkbox, 0, flag=wx.EXPAND | wx.ALL, border=b)

        self.SetSizerAndFit(sizer)

    # -----------------------------------------------------------------------

    def _on_broom(self, event):
        self.FindWindow("text_entry").SetValue("")

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): one of the methods in TagCompare
               - value (list of str): the pattern to find

        """
        radiobox = self.FindWindow("radio_functions")
        idx = radiobox.GetSelection()
        label = radiobox.GetStringSelection()
        given_fct = sppasTagStringPanel.choices[idx][1]

        # Fill the resulting dict
        prepend_fct = ""

        if given_fct != "regexp":
            # prepend "not_" if reverse
            if "not" in label:
                prepend_fct += "not_"
            # prepend "i" if case-insensitive
            if self.FindWindow("check_case").GetValue() is False:
                prepend_fct += "i"

        return "tag", prepend_fct+given_fct, [self.FindWindow("text_entry").GetValue()]

# ---------------------------------------------------------------------------


class sppasTagIntegerPanel(sppasPanel):
    """Panel to get a filter on a sppasTag if its type is 'int'.

    """

    choices = (
               (MSG_EQUAL, "equal"),
               (MSG_GT, "greater"),
               (MSG_LT, "lower"),
             )

    def __init__(self, parent):
        super(sppasTagIntegerPanel, self).__init__(parent)
        top_label = sppasStaticText(self, label=MSG_TAG_TYPE_INT)
        h = self.get_font_height()

        functions = [row[0] for row in sppasTagIntegerPanel.choices]
        self.radiobox = sppasRadioBoxPanel(
            self,
            choices=functions,
            style=wx.RA_SPECIFY_COLS)
        self.radiobox.SetSelection(1)
        self.radiobox.SetMinSize(wx.Size(-1, ((len(functions)*2)+1)*h))

        self.text = sppasTextCtrl(self, value="0")

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        b = sppasPanel.fix_size(6)
        sizer.Add(top_label, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.radiobox, 0, flag=wx.EXPAND | wx.ALL, border=b*2)
        sizer.Add(self.text, 0, flag=wx.EXPAND | wx.ALL, border=b)
        self.SetSizerAndFit(sizer)

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): one of the methods in Compare
               - values (list): integer to compare

        """
        idx = self.radiobox.GetSelection()
        given_fct = sppasTagIntegerPanel.choices[idx][1]
        str_value = self.text.GetValue()
        try:
            value = int(str_value)
        except ValueError:
            wx.LogError("{:s} can't be converted to an integer"
                        "".format(str_value))
            value = 0

        return "tag", given_fct, [value]

# ---------------------------------------------------------------------------


class sppasTagFloatPanel(sppasPanel):
    """Panel to get a filter on a sppasTag if its type is 'float'.

    """

    choices = (
               (MSG_EQUAL, "equal"),
               (MSG_GT, "greater"),
               (MSG_LT, "lower"),
             )

    def __init__(self, parent):
        """Create a tag filter panel, for tags of type float.

         :param parent: (wx.Window)

         """
        super(sppasTagFloatPanel, self).__init__(parent)
        top_label = sppasStaticText(self, label=MSG_TAG_TYPE_FLOAT)
        h = self.get_font_height()

        functions = [row[0] for row in sppasTagIntegerPanel.choices]
        self.radiobox = sppasRadioBoxPanel(
            self,
            choices=functions,
            style=wx.RA_SPECIFY_COLS)
        self.radiobox.SetSelection(0)
        self.radiobox.SetMinSize(wx.Size(-1, ((len(functions)*2)+1)*h))

        self.text = sppasTextCtrl(self, value="0.")

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        b = sppasPanel.fix_size(6)
        sizer.Add(top_label, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.radiobox, 0, flag=wx.EXPAND | wx.ALL, border=b*2)
        sizer.Add(self.text, 0, flag=wx.EXPAND | wx.ALL, border=b)
        self.SetSizerAndFit(sizer)

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): one of the methods in Compare
               - values (list): patterns to find

        """
        idx = self.radiobox.GetSelection()
        given_fct = sppasTagIntegerPanel.choices[idx][1]
        str_value = self.text.GetValue()
        try:
            value = float(str_value)
        except ValueError:
            wx.LogError("{:s} can't be converted to a float"
                        "".format(str_value))
            value = 0.

        return "tag", given_fct, [value]

# ---------------------------------------------------------------------------


class sppasTagBooleanPanel(sppasPanel):
    """Panel to get a filter on a sppasTag if its type is 'boolean'.

    """

    def __init__(self, parent):
        """Create a tag filter panel, for tags of type boolean.

        :param parent: (wx.Window)

        """
        super(sppasTagBooleanPanel, self).__init__(parent)
        top_label = sppasStaticText(self, label=MSG_TAG_TYPE_BOOL)
        h = self.get_font_height()

        self.radiobox = sppasRadioBoxPanel(
            self, choices=[MSG_FALSE, MSG_TRUE], style=wx.RA_SPECIFY_COLS)
        self.radiobox.SetSelection(1)
        self.radiobox.SetMinSize(wx.Size(-1, (5*h)))

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        b = sppasPanel.fix_size(6)
        sizer.Add(top_label, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.radiobox, 0, flag=wx.EXPAND | wx.ALL, border=b*2)
        self.SetSizerAndFit(sizer)

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): bool
               - values (list): patterns to find

        """
        # False is at index 0 so that bool(index) gives the value
        idx = self.radiobox.GetSelection()
        return "tag", "bool", [bool(idx)]

# ----------------------------------------------------------------------------


class LengthTextValidator(wx.Validator):
    """Check if the TextCtrl is valid for a pattern.

    If the TextCtrl is not valid, the background becomes pinky.

    """

    def __init__(self):
        super(LengthTextValidator, self).__init__()
        self.__max_length = 256
        self.__min_length = 1

    def SetMinLength(self, value):
        self.__min_length = int(value)

    def SetMaxLength(self, value):
        self.__max_length = int(value)

    def Clone(self):
        # Required method for validator
        return LengthTextValidator()

    def TransferToWindow(self):
        # Prevent wxDialog from complaining.
        return True

    def TransferFromWindow(self):
        # Prevent wxDialog from complaining.
        return True

    def Validate(self, win=None):
        text_ctrl = self.GetWindow()
        text = text_ctrl.GetValue().strip()
        if self.__min_length < len(text) > self.__max_length:
            text_ctrl.SetBackgroundColour("pink")
            text_ctrl.SetFocus()
            text_ctrl.Refresh()
            return False

        try:
            text_ctrl.SetBackgroundColour(wx.GetApp().settings.bg_color)
        except:
            text_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        text_ctrl.Refresh()
        return True
