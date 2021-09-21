# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_analyze.filters.tagfilter.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A dialog to fix filters on tags of annotations of a tier.

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
from sppas.src.ui.phoenix.windows.book import sppasNotebook
from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagBooleanPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagIntegerPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagFloatPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagStringsPanel

# --------------------------------------------------------------------------


def _(message):
    return u(msg(message, "ui"))


MSG_TAG_FILTER = _("Filter on tags of annotations")

# ---------------------------------------------------------------------------


class sppasTagFilterDialog(sppasDialog):
    """Dialog to get a filter on a sppasTag.

    """

    def __init__(self, parent):
        """Create a string filter dialog.

        :param parent: (wx.Window)

        """
        super(sppasTagFilterDialog, self).__init__(
            parent=parent,
            title="+ Tag filter",
            style=wx.DEFAULT_FRAME_STYLE)

        self.CreateHeader(MSG_TAG_FILTER, "tier_filter_add_tag")
        self._create_content()
        self.CreateActions([wx.ID_CANCEL, wx.ID_OK])

        self.LayoutComponents()
        self.SetSizerAndFit(self.GetSizer())
        self.CenterOnParent()

    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data defined by the user.

        :returns: (tuple) with:
               - type (str): tag
               - function (str): one of the methods in Compare
               - values (list): patterns to find

        """
        notebook = self.FindWindow("content")
        page_idx = notebook.GetSelection()
        data = notebook.GetPage(page_idx).get_data()
        return data

    # -----------------------------------------------------------------------
    # Methods to construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the message dialog.

        notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, ...) not used because it
        is bugged under MacOS (do not display the page content).

        """
        # Make the notebook to show each possible type of tag
        notebook = sppasNotebook(self, name="content")

        # Create and add the pages to the notebook
        page1 = sppasTagStringsPanel(notebook)
        notebook.AddPage(page1, " String ")
        page2 = sppasTagIntegerPanel(notebook)
        notebook.AddPage(page2, " Integer ")
        page3 = sppasTagFloatPanel(notebook)
        notebook.AddPage(page3, " Float ")
        page4 = sppasTagBooleanPanel(notebook)
        notebook.AddPage(page4, " Boolean ")

        w, h = page1.GetMinSize()
        notebook.SetMinSize(wx.Size(w, h+(sppasPanel().get_font_height()*4)))
        self.SetContent(notebook)

# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(TestPanel, self).__init__(parent, pos=pos, size=size,
                                        name="Tag Filter")

        btn = wx.Button(self, label="Tag filter")
        btn.SetMinSize(wx.Size(150, 40))
        btn.SetPosition(wx.Point(10, 10))
        self.Bind(wx.EVT_BUTTON, self._process_event)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        dlg = sppasTagFilterDialog(self)
        response = dlg.ShowModal()
        if response == wx.ID_OK:
            f = dlg.get_data()
            if len(f[1].strip()) > 0:
                wx.LogMessage("'tag': filter='{:s}'; value='{:s}'"
                              "".format(f[1], str(f[2])))
            else:
                wx.LogError("Empty input pattern.")
        dlg.Destroy()
