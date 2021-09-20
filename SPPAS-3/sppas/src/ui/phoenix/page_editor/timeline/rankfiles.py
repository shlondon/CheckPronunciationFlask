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

    ui.phoenix.page_editor.timeline.rankfiles.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A dialog to sort files.

"""

import wx
import os.path

from sppas.src.config import msg
from sppas.src.utils import u

from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.dialogs import sppasDialog
from sppas.src.ui.phoenix.windows.buttons import BitmapTextButton
from sppas.src.ui.phoenix.windows.listctrl import LineListCtrl
from sppas.src.ui.phoenix.windows.line import sppasStaticLine

# ----------------------------------------------------------------------------


MSG_TITLE = u(msg("Sort files", "ui"))
MSG_UP_FILE = u(msg("File up", "ui"))
MSG_DOWN_FILE = u(msg("File down", "ui"))
MSG_APPLY = u(msg("Apply", "ui"))

# ----------------------------------------------------------------------------


class sppasRankFilesDialog(sppasDialog):
    """A dialog to list filenames and sort them manually.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    """

    def __init__(self, parent, files=(), bg_colors=(), **kwargs):
        """Create a dialog with a message.

        :param parent: (wx.Window)
        :param files: (list) The list of file names to display in this dialog.

        """
        super(sppasRankFilesDialog, self).__init__(
            parent=parent,
            style=wx.CAPTION | wx.FRAME_TOOL_WINDOW | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.STAY_ON_TOP)

        self.CreateHeader(MSG_TITLE, icon_name="sort")
        self._create_content(files, bg_colors)
        self._create_actions()

        # Fix frame properties
        self.SetMinSize(wx.Size(sppasDialog.fix_size(420),
                                sppasDialog.fix_size(240)))
        self.LayoutComponents()
        self.CenterOnParent()
        self.FadeIn()

    # -----------------------------------------------------------------------

    def get_files(self):
        """Return the ranked list of files."""
        files = list()
        for i in range(self.listctrl.GetItemCount()):
            fn = self.listctrl.GetItemText(i, 0)
            pn = self.listctrl.GetItemText(i, 1)
            files.append(os.path.join(pn, fn))

        return files

    # -----------------------------------------------------------------------

    def _create_content(self, files, bg_colors=()):
        """Create the content of the dialog.

        """
        if len(files) != len(bg_colors):
            bg_colors = list()

        # Create a listctrl to display the list of filenames
        listctrl = LineListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        listctrl.SetAlternateRowColour(False)

        # Create columns of the list
        listctrl.InsertColumn(0, "Name")
        listctrl.InsertColumn(1, "Path")

        # Fill in the lines
        if len(files) > 0:
            for filename in files:
                idx = listctrl.InsertItem(listctrl.GetItemCount(), os.path.basename(filename))
                listctrl.SetItem(idx, 1, os.path.dirname(filename))
                if len(bg_colors) > 0:
                    listctrl.SetItemBackgroundColour(idx, bg_colors[idx])
            listctrl.Select(0, on=1)

        # Adjust columns width
        listctrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        listctrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        self.SetContent(listctrl)

    # -----------------------------------------------------------------------

    def _create_actions(self):
        """Create the content of the frame.

        Content is made of a menu, an area for panels and action buttons.

        """
        ap = sppasPanel(self)
        settings = wx.GetApp().settings
        ap.SetMinSize(wx.Size(-1, settings.action_height))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        up_btn = self._create_button(ap, MSG_UP_FILE, "arrow_move_up")
        up_btn.Bind(wx.EVT_BUTTON, lambda evt: self._up_file())
        down_btn = self._create_button(ap, MSG_DOWN_FILE, "arrow_move_down")
        down_btn.Bind(wx.EVT_BUTTON, lambda evt: self._down_file())

        apply_btn = self._create_button(ap, MSG_APPLY, "yes")
        apply_btn.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_OK))

        sizer.Add(up_btn, 1, wx.EXPAND)
        sizer.Add(self._vert_line(ap), 0, wx.EXPAND)
        sizer.Add(down_btn, 1, wx.EXPAND)
        sizer.Add(self._vert_line(ap), 0, wx.EXPAND)
        sizer.Add(apply_btn, 3, wx.EXPAND)
        ap.SetSizer(sizer)

        self.SetActions(ap)

    # -----------------------------------------------------------------------

    def _create_button(self, parent, text, icon):
        btn = BitmapTextButton(parent, label=text, name=icon)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetLabelPosition(wx.RIGHT)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(h//4)
        btn.SetFocusColour(wx.Colour(128, 128, 128, 128))
        btn.SetSpacing(sppasPanel.fix_size(h//2))
        btn.SetMinSize(wx.Size(h*10, h*2))

        return btn

    # ------------------------------------------------------------------------

    def _vert_line(self, parent):
        """Return a vertical static line."""
        line = sppasStaticLine(parent, orient=wx.LI_VERTICAL)
        line.SetMinSize(wx.Size(1, -1))
        line.SetSize(wx.Size(1, -1))
        line.SetPenStyle(wx.PENSTYLE_SOLID)
        line.SetDepth(1)
        return line

    # ------------------------------------------------------------------------

    @property
    def listctrl(self):
        return self.FindWindow("content")

    # ------------------------------------------------------------------------

    def _up_file(self):
        """The selected file will go up."""
        # Get the index of the currently selected item
        selected = self.listctrl.GetFirstSelected()
        if selected == -1:
            return

        if selected != 0:
            # Get the content of the previous item
            fn_prev = self.listctrl.GetItemText(selected-1, col=0)
            path_prev = self.listctrl.GetItemText(selected-1, col=1)
            color_prev = self.listctrl.GetItemBackgroundColour(selected-1)

            # Replace the previous item content by the selected one
            self.listctrl.SetItem(selected - 1, 0, self.listctrl.GetItemText(selected, col=0))
            self.listctrl.SetItem(selected - 1, 1, self.listctrl.GetItemText(selected, col=1))
            color_selected = self.listctrl.GetItemBackgroundColour(selected)

            # Replace the currently selected item with the previous
            self.listctrl.SetItem(selected, 0, fn_prev)
            self.listctrl.SetItem(selected, 1, path_prev)

            # Replace colors
            self.listctrl.SetItemBackgroundColour(selected-1, color_selected)
            self.listctrl.SetItemBackgroundColour(selected, color_prev)

            # Keep the same selected content
            self.listctrl.Select(selected - 1, on=1)

    # ------------------------------------------------------------------------

    def _down_file(self):
        """The selected file will go down."""
        # Get the index of the currently selected item
        selected = self.listctrl.GetFirstSelected()
        if selected == -1:
            return

        if selected + 1 < self.listctrl.GetItemCount():
            # Get the content of the next item
            fn_next = self.listctrl.GetItemText(selected + 1, col=0)
            path_next = self.listctrl.GetItemText(selected + 1, col=1)
            color_next = self.listctrl.GetItemBackgroundColour(selected+1)

            # Replace the next item content by the selected one
            self.listctrl.SetItem(selected + 1, 0, self.listctrl.GetItemText(selected, col=0))
            self.listctrl.SetItem(selected + 1, 1, self.listctrl.GetItemText(selected, col=1))
            color_selected = self.listctrl.GetItemBackgroundColour(selected)

            # Replace the currently selected item with the previous
            self.listctrl.SetItem(selected, 0, fn_next)
            self.listctrl.SetItem(selected, 1, path_next)

            # Replace colors
            self.listctrl.SetItemBackgroundColour(selected+1, color_selected)
            self.listctrl.SetItemBackgroundColour(selected, color_next)

            # Keep the same selected content
            self.listctrl.Select(selected + 1, on=1)

# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test Rank Files Dialog")

        b = wx.Button(self, label="Open dialog", pos=(10, 10), size=(128, 64))
        b.Bind(wx.EVT_BUTTON, self._on_dlg)

    def _on_dlg(self, evt):
        files = list()
        files.append("/me/audios/file1.wav")
        files.append("/the/path/to/the/file/file2.wave")
        files.append("/azerty/file3.txt")
        files.append("/home/sweet/home/file4.xxx")
        files.append("/somewhere/in/computer/file5.textgrid")
        files.append("/me/videos/file6.mp4")
        files.append("/me/images/file7.png")
        dlg = sppasRankFilesDialog(self, files)
        dlg.ShowModal()
        sorted_files = dlg.get_files()
        dlg.DestroyFadeOut()
        print(sorted_files)
