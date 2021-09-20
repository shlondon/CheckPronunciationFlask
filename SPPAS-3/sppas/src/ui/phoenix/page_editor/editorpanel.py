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

    ui.phoenix.page_editor.editor_panel.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Main panel of the Editor page.

"""

import os
import wx

from sppas.src.config import msg
from sppas.src.config import paths
from sppas.src.utils import u

from ..windows import sppasPanel
from ..windows import sppasSplitterWindow

from .listanns.tiersanns import sppasTiersEditWindow
from .listanns import EVT_LISTANNS_VIEW
from .timeline import sppasTimelinePanel
from .timeline import EVT_TIMELINE_VIEW

# ---------------------------------------------------------------------------
# List of displayed messages:


def _(message):
    return u(msg(message, "ui"))


MSG_CLOSE = _("Close")

CLOSE_CONFIRM = _("The file contains not saved work that will be "
                  "lost. Are you sure you want to close?")

# ----------------------------------------------------------------------------


class EditorPanel(sppasSplitterWindow):
    """Panel to display opened files and their content in a time-line style.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020 Brigitte Bigi

    """

    def __init__(self, parent, name="editor_panel"):
        super(EditorPanel, self).__init__(
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.BORDER_NONE | wx.NO_FULL_REPAINT_ON_RESIZE,
            name=name)

        self._create_content()

        # The event emitted by the sppasTimeEditFilesPanel
        self.Bind(EVT_TIMELINE_VIEW, self._process_timeline_action)
        # The event emitted by the sppasTiersEditWindow
        self.Bind(EVT_LISTANNS_VIEW, self._process_listanns_action)

        # Look&feel
        try:
            self.SetBackgroundColour(wx.GetApp().settings.bg_color)
            self.SetForegroundColour(wx.GetApp().settings.fg_color)
            self.SetFont(wx.GetApp().settings.text_font)
        except AttributeError:
            self.InheritAttributes()

        self.Layout()

    # -----------------------------------------------------------------------

    def swap_panels(self):
        """Swap the panels of the splitter."""
        win_1 = self.GetWindow1()
        win_2 = self.GetWindow2()
        w, h = win_2.GetSize()
        self.Unsplit(toRemove=win_1)
        self.Unsplit(toRemove=win_2)
        self.SplitHorizontally(win_2, win_1, h)

        if win_1 == self._listview:
            self.SetSashGravity(0.6)
        else:
            self.SetSashGravity(0.4)

        self.UpdateSize()

    # -----------------------------------------------------------------------

    def swap_annlist_panels(self):
        """Swap the panels of the listview splitter."""
        self._listview.swap_panels()

    # -----------------------------------------------------------------------
    # Public methods to manage files and tiers
    # -----------------------------------------------------------------------

    def get_files(self):
        """Return the list of filenames this panel is displaying."""
        return self._timeview.get_files()

    # -----------------------------------------------------------------------

    def append_file(self, name):
        """Add a file and display its content.

        Do not refresh/layout the GUI.

        :param name: (str)
        :raise: ValueError

        """
        # If the file is a media, we'll receive an action "media_loaded".
        # If the file is a trs, we'll receive the action "tiers_added", then
        # the tiers will be added to the listview.
        self._timeview.append_file(name)

    # -----------------------------------------------------------------------

    def save_file(self, name):
        """Save a file.

        :param name: (str)
        :return: (bool) The file was saved or not

        """
        res = self._timeview.save_file(name)
        return res

    # -----------------------------------------------------------------------

    def is_modified(self, name=None):
        """Return True if the content of the file has changed.

        :param name: (str) Name of a file or none for any file.

        """
        return self._timeview.is_modified(name)

    # -----------------------------------------------------------------------

    def remove_file(self, name, force=False):
        """Remove a panel corresponding to the name of a file.

        :param name: (str)
        :param force: (bool) Force to remove, even if a file is modified
        :return: (bool) The file was removed or not

        """
        if self._timeview.is_trs(name):
            tiers = self._timeview.get_tier_list(name)
            self._listview.remove_tiers(name, tiers)

        self._timeview.remove_file(name, force)
        self._timeview.Layout()
        return True

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the main content of the window.

        - Window 1 of the splitter: a ListCtrl of each tier in a notebook;
        - Window 2 of the splitter: an annotation editor.

        """
        w1 = sppasTiersEditWindow(self, orient=wx.HORIZONTAL, name="tiersanns_panel")
        w2 = sppasTimelinePanel(self, name="timeline_panel")

        # Fix size&layout
        w, h = self.GetSize()
        self.SetMinimumPaneSize(sppasPanel.fix_size(100))
        self.SplitHorizontally(w1, w2, sppasPanel.fix_size(h // 2))
        self.SetSashGravity(0.4)

    # -----------------------------------------------------------------------
    # A private/quick access to children windows
    # -----------------------------------------------------------------------

    @property
    def _listview(self):
        return self.FindWindow("tiersanns_panel")

    @property
    def _timeview(self):
        return self.FindWindow("timeline_panel")

    # -----------------------------------------------------------------------

    def _process_timeline_action(self, event):
        """Process an action event from one of the timeline view child panel.

        :param event: (wx.Event)

        """
        filename = event.filename
        action = event.action
        value = event.value
        wx.LogDebug("{:s} received an event action {:s} of file {:s} with value {:s}"
                    "".format(self.GetName(), action, filename, str(value)))

        if action == "tier_selected":
            # value of the event is the name of the tier
            ann_index = self._timeview.get_selected_annotation()
            self._listview.set_selected_tiername(filename, value, ann_index)

        elif action == "tiers_added":
            self._listview.add_tiers(filename, value)

        elif action == "save":
            self.save_file(filename)

        elif action == "ann_create":
            self._listview.inserted_at(value)

        elif action == "ann_update":
            self._listview.update(value)

        else:
            # we just need to layout ourself
            self.UpdateSize()
            # other actions (close) are ignored.
            # They will be handled by the parent.
            event.Skip()

    # -----------------------------------------------------------------------

    def _process_listanns_action(self, event):
        """Process an action event from the list view.

        :param event: (wx.Event)

        """
        filename = event.filename
        action = event.action
        value = event.value

        if action == "ann_create":
            self._timeview.update_ann(filename, value, what="create")

        elif action == "ann_delete":
            self._timeview.update_ann(filename, value, what="delete")

        elif action == "ann_update":
            self._timeview.update_ann(filename, value, what="update")

        # In all cases, update the selected annotation of the timeview
        tier_name = self._listview.get_selected_tiername()
        self._timeview.set_selected_tiername(filename, tier_name)
        idx = self._listview.get_selected_annotation()
        self._timeview.set_selected_annotation(idx)

# ----------------------------------------------------------------------------
# Panel for tests
# ----------------------------------------------------------------------------


class TestPanel(EditorPanel):
    TEST_FILES = (
        os.path.join(paths.samples, "samples-fra", "F_F_B003-P8.wav"),
        # "C:\\Users\\bigi\\Videos\\agay_2.mp4",
        # os.path.join("/Users/bigi/Movies/Monsters_Inc.For_the_Birds.mpg"),
        # os.path.join("/E/Videos/Monsters_Inc.For_the_Birds.mpg"),
        # os.path.join(paths.samples, "COPYRIGHT.txt"),
        os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra"),
        os.path.join(paths.samples, "samples-fra", "F_F_B003-P8-merge.TextGrid"),
        os.path.join(paths.samples, "toto.xxx"),
        # os.path.join(paths.samples, "toto.ogg")
    )

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="Main Editor Panel")

        for filename in TestPanel.TEST_FILES:
            self.append_file(filename)