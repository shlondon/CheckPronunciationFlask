# -*- coding: UTF-8 -*-
"""
:filename: src.ui.phoenix.page_analyze.filters.durfilter.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A dialog to fix filters on the nb of labels of anns of a tier.

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

from sppas.src.ui.phoenix.windows.dialogs import sppasDialog
from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.text import sppasStaticText
from sppas.src.ui.phoenix.windows import sppasRadioBoxPanel

# --------------------------------------------------------------------------


def _(message):
    return u(msg(message, "ui"))


MSG_NLAB_FILTER = _("Filter on number of labels of annotations")

MSG_NLAB = _("The number of labels is:")

MSG_EQUAL = _("equal to")
MSG_NOT_EQUAL = _("not equal to")
MSG_GT = _("greater than")
MSG_LT = _("less than")
MSG_GE = _("greater or equal to")
MSG_LE = _("less or equal to")
MSG_VALUE = _("this value:")

# ---------------------------------------------------------------------------


class sppasLabelNumberFilterDialog(sppasDialog):
    """Dialog to get a filter on number of labels.

    """

    choices = (
        (MSG_EQUAL, "leq"),
        (MSG_NOT_EQUAL, "lne"),
        (MSG_GT, "lgt"),
        (MSG_LT, "llt"),
        (MSG_GE, "lge"),
        (MSG_LE, "lle")
    )

    def __init__(self, parent):
        """Create a filter dialog.

        :param parent: (wx.Window)

        """
        super(sppasLabelNumberFilterDialog, self).__init__(
            parent=parent,
            title="+ Nb lab filter",
            style=wx.DEFAULT_FRAME_STYLE)

        self.CreateHeader(MSG_NLAB_FILTER, "tier_filter_add_nlab")
        self._create_content()
        self.CreateActions([wx.ID_CANCEL, wx.ID_OK])

        self.LayoutComponents()
        self.SetSizerAndFit(self.GetSizer())
        self.CenterOnParent()

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with
               type (str): dur
               function (str): one of the choices
               values (list): time value (represented by a 'str')

        """
        idx = self.radiobox.GetSelection()
        given_fct = sppasLabelNumberFilterDialog.choices[idx][1]
        value = self.ctrl.GetValue()
        return "nlab", given_fct, [value]

    # -----------------------------------------------------------------------
    # Method to construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the message dialog."""
        panel = sppasPanel(self, name="content")

        top_label = sppasStaticText(panel, label=MSG_NLAB)
        top_label.SetMinSize(wx.Size(sppasPanel.fix_size(320), -1))
        bottom_label = sppasStaticText(panel, label=MSG_VALUE)

        choices = [row[0] for row in sppasLabelNumberFilterDialog.choices]
        self.radiobox = sppasRadioBoxPanel(panel, choices=choices, style=wx.RA_SPECIFY_COLS)
        self.radiobox.SetSelection(0)

        self.ctrl = wx.SpinCtrl(panel, value="", min=0, initial=0)

        # Layout
        b = sppasPanel.fix_size(6)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(bottom_label, 0, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=b)
        hbox.Add(self.ctrl, 1, flag=wx.EXPAND | wx.ALL, border=b)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_label, 0, flag=wx.EXPAND | wx.ALL, border=b)
        sizer.Add(self.radiobox, 1, flag=wx.EXPAND | wx.ALL, border=2*b)
        sizer.Add(hbox, 0, flag=wx.EXPAND | wx.ALL, border=0)

        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        self.SetContent(panel)

# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(TestPanel, self).__init__(parent, pos=pos, size=size,
                                        name="Nb of labels Filter")

        btn = wx.Button(self, label="Nb Labels filter")
        btn.SetMinSize(wx.Size(150, 40))
        btn.SetPosition(wx.Point(10, 10))
        self.Bind(wx.EVT_BUTTON, self._process_event)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        dlg = sppasLabelNumberFilterDialog(self)
        response = dlg.ShowModal()
        if response == wx.ID_OK:
            f = dlg.get_data()
            if len(f[1].strip()) > 0:
                wx.LogMessage("'nlab': filter='{:s}'; value='{:s}'"
                              "".format(f[1], str(f[2])))
            else:
                wx.LogError("Empty input pattern.")
        dlg.Destroy()
