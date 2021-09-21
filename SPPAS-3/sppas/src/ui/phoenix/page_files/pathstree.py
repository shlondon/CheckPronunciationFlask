# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_files.pathstree.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  The panel to manage the tree of files.

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

import os
import wx

from sppas.src.config import paths
from sppas.src.config import msg

from ..windows import sppasPanel
from ..windows import sppasToolbar
from ..windows import sppasStaticLine
from ..windows import YesNoQuestion, Information
from ..windows import sppasFileDialog
from ..main_events import DataChangedEvent, EVT_DATA_CHANGED

from .filesviewctrl import FileTreeViewPanel

# ---------------------------------------------------------------------------
# List of displayed messages:

FLS_TITLE = msg("Files: ", "ui")
FLS_ACT_ADD = msg("Add", "ui")
FLS_ACT_REM = msg("Remove checked", "ui")
FLS_ACT_DEL = msg("Delete checked", "ui")

FLS_MSG_CONFIRM_DEL = msg("Are you sure you want to delete {:d} files?")

# ----------------------------------------------------------------------------


class PathsTreePanel(sppasPanel):
    """Manage the tree of files and actions to perform on them.

    """

    HIGHLIGHT_COLOUR = wx.Colour(228, 128, 128, 196)

    def __init__(self, parent, name=wx.PanelNameStr):
        super(PathsTreePanel, self).__init__(
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.NO_FULL_REPAINT_ON_RESIZE,
            name=name)

        self.__current_dir = paths.samples
        self._create_content()
        self._setup_events()

        self.SetMinSize(wx.Size(sppasPanel.fix_size(320), -1))
        self.SetAutoLayout(True)
        self.Layout()

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Override. """
        wx.Panel.SetForegroundColour(self, colour)
        for c in self.GetChildren():
            if c.GetName() != "hline":
                c.SetForegroundColour(colour)

    # -----------------------------------------------------------------------
    # Public methods to access the data
    # -----------------------------------------------------------------------

    def get_data(self):
        """Return the data like they are currently stored into the model."""
        return self._filestree.get_data()

    # ------------------------------------------------------------------------

    def set_data(self, data):
        """Assign a new data instance to display to this panel.

        :param data: (sppasWorkspace)

        """
        self._filestree.set_data(data)

    # ------------------------------------------------------------------------
    # Private methods to construct the panel.
    # ------------------------------------------------------------------------

    def _create_content(self):
        """Create the main content."""
        tb = self.__create_toolbar()
        fv = FileTreeViewPanel(self, name="filestree")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tb, proportion=0, flag=wx.EXPAND, border=0)
        sizer.Add(self.__create_hline(), 0, wx.EXPAND, 0)
        sizer.Add(fv, proportion=1, flag=wx.EXPAND, border=0)
        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    @property
    def _filestree(self):
        return self.FindWindow("filestree")

    # -----------------------------------------------------------------------

    def __create_toolbar(self):
        """Create the toolbar."""
        tb = sppasToolbar(self)
        tb.set_focus_color(PathsTreePanel.HIGHLIGHT_COLOUR)
        tb.AddTitleText(FLS_TITLE, PathsTreePanel.HIGHLIGHT_COLOUR)
        tb.AddButton("files-add", FLS_ACT_ADD)
        tb.AddButton("files-remove", FLS_ACT_REM)
        tb.AddButton("files-delete", FLS_ACT_DEL)

        return tb

    # -----------------------------------------------------------------------

    def __create_hline(self):
        """Create an horizontal line, used to separate the panels."""
        line = sppasStaticLine(self, orient=wx.LI_HORIZONTAL, name="hline")
        line.SetMinSize(wx.Size(-1, 20))
        line.SetPenStyle(wx.PENSTYLE_SHORT_DASH)
        line.SetDepth(1)
        line.SetForegroundColour(self.HIGHLIGHT_COLOUR)
        return line

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # The user clicked (LeftDown - LeftUp) an action button of the toolbar
        self.Bind(wx.EVT_BUTTON, self._process_action)

        # Changes occurred in the child files tree
        self.Bind(EVT_DATA_CHANGED, self._process_data_changed)

    # ------------------------------------------------------------------------

    def notify(self):
        """Send the EVT_DATA_CHANGED to the parent."""
        if self.GetParent() is not None:
            data = self._filestree.get_data()
            evt = DataChangedEvent(data=data)
            evt.SetEventObject(self)
            wx.PostEvent(self.GetParent(), evt)

    # ------------------------------------------------------------------------
    # Callbacks to events
    # ------------------------------------------------------------------------

    def _process_data_changed(self, event):
        sender = event.GetEventObject()
        if sender is self._filestree:
            self.notify()

    # ------------------------------------------------------------------------

    def _process_action(self, event):
        """Process an action of a button.

        :param event: (wx.Event)

        """
        name = event.GetEventObject().GetName()

        if name == "files-add":
            self.add()

        elif name == "files-remove":
            self.remove()

        elif name == "files-delete":
            self.delete()

        event.Skip()

    # ------------------------------------------------------------------------
    # GUI methods to perform actions on the data
    # ------------------------------------------------------------------------

    def add(self):
        """Add user-selected files into the files viewer."""
        filenames = list()
        dlg = sppasFileDialog(self)
        if os.path.exists(self.__current_dir):
            dlg.SetDirectory(self.__current_dir)
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetPaths()
        dlg.Destroy()

        if len(filenames) > 0:
            added = self._filestree.AddFiles(filenames)
            if added > 0:
                self.__current_dir = os.path.dirname(filenames[0])
                self.notify()

    # ------------------------------------------------------------------------

    def remove(self):
        """Remove the checked files of the file viewer."""
        data = self.get_data()
        if data.is_empty():
            wx.LogMessage('No files in data. Nothing to remove.')
            return

        removed = self._filestree.RemoveCheckedFiles()
        if removed:
            self.notify()

    # ------------------------------------------------------------------------

    def delete(self):
        """Move into the trash the checked files of the file viewer."""
        data = self.get_data()
        if data.is_empty():
            wx.LogMessage('No files in data. Nothing to delete.')
            return

        checked_files = self._filestree.GetCheckedFiles()
        if len(checked_files) == 0:
            Information('None of the files are selected to be deleted.')
            return

        # User must confirm to really delete files
        message = FLS_MSG_CONFIRM_DEL.format(len(checked_files))
        response = YesNoQuestion(message)
        if response == wx.ID_YES:
            deleted = self._filestree.DeleteCheckedFiles()
            if deleted:
                self.notify()
        elif response == wx.ID_NO:
            wx.LogMessage('Response is no. No file deleted.')

# ----------------------------------------------------------------------------


class TestPanel(PathsTreePanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="FilesManager")
        self.add_one_test_data()

    # ------------------------------------------------------------------------

    def add_one_test_data(self):
        self._filestree.AddFiles([os.path.abspath(__file__)])

    # ------------------------------------------------------------------------

    def add_test_data(self):
        here = os.path.abspath(os.path.dirname(__file__))
        self._filestree.AddFiles([os.path.abspath(__file__)])
        self._filestree.LockFiles([os.path.abspath(__file__)])

        for f in os.listdir(here):
            fullname = os.path.join(here, f)
            if os.path.isfile(fullname):
                wx.LogMessage('Add {:s}'.format(fullname))
                nb = self._filestree.AddFiles([fullname])
                wx.LogMessage(" --> {:d} files added.".format(nb))
