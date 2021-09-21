# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_editor.searchtag.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A dialog to search for a tag in a set of tiers.

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
import wx.lib.newevent

from sppas.src.config import msg
from sppas.src.config import paths
from sppas.src.utils import u
from sppas.src.structs import sppasBaseFilters
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTagCompare

from sppas.src.ui.phoenix.windows import sb
from sppas.src.ui.phoenix.windows import sppasDialog
from sppas.src.ui.phoenix.windows import sppasStaticText, sppasTextCtrl
from sppas.src.ui.phoenix.windows.book import sppasNotebook
from sppas.src.ui.phoenix.windows.book import sppasChoicebook
from sppas.src.ui.phoenix.windows import sppasPanel
from sppas.src.ui.phoenix.windows import sppasStaticLine
from sppas.src.ui.phoenix.windows import BitmapTextButton
from sppas.src.ui.phoenix.windows import sppasCheckBoxPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagStringPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagIntegerPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagFloatPanel
from sppas.src.ui.phoenix.panel_shared import sppasTagBooleanPanel

# ---------------------------------------------------------------------------


SearchViewEvent, EVT_SEARCH_VIEW = wx.lib.newevent.NewEvent()
SearchViewCommandEvent, EVT_SEARCH_VIEW_COMMAND = wx.lib.newevent.NewCommandEvent()

# ----------------------------------------------------------------------------


def _(message):
    return u(msg(message, "ui"))


MSG_HEADER_SEARCH = _("Search for tags in given tiers")
MSG_ACTION_CLOSE = _("Close")
MSG_ACTION_FORWARD = _("Forward")
MSG_ACTION_BACKWARD = _("Backward")

# --------------------------------------------------------------------------


class sppasSearchTagDialog(sppasDialog):
    """A dialog to search for tags matching a given pattern in given tiers.

    """

    def __init__(self, parent, name="dlg_search"):
        """Create a dialog.

        :param parent: (wx.Window)

        """
        super(sppasSearchTagDialog, self).__init__(
            parent=parent,
            title="Search...",
            style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.STAY_ON_TOP,
            name=name)

        # List of tiers this dialog is working with
        # This is a list of tuple(filename, sppasTier)
        self.__tiers = list()
        self.__selected_tier = -1
        self.__selected_ann = -1
        self.__comparator = sppasTagCompare()

        # Create all the items
        self.CreateHeader(MSG_HEADER_SEARCH, "search")
        self._create_content()
        self.SetActions(SearchActionsPanel(self))

        # Manage the events
        self.SetAffirmativeId(wx.ID_CLOSE)
        self._setup_events()

        # Create a sizer and organize the items: header/content/actions
        self.LayoutComponents()
        self.GetSizer().Fit(self)
        self.SetMinSize(wx.Size(sppasPanel.fix_size(320), sppasPanel.fix_size(200)))

        self.SetFocus()
        # self.CenterOnParent()

    # -----------------------------------------------------------------------
    # Public methods to manage files and tiers
    # -----------------------------------------------------------------------

    def add_tiers(self, filename, tiers):
        """Add a set of tiers of the given file.

        :param filename: (str)
        :param tiers: (list of sppasTier)

        """
        print("Add tiers into the search dialog...")
        for tier in tiers:
            contains = False
            for f, t in self.__tiers:
                if f == filename and t is tier:
                    contains = True
                    break
            if contains is False:
                self.__tiers.append((filename, tier))
                self.__cbt.Append(tier.get_name())

        self.update_checkable_tiers()

    # -----------------------------------------------------------------------

    def remove_tiers(self, filename, tiers):
        """Remove a set of tiers of the given file.

        :param filename: (str)
        :param tiers: (list of sppasTier)

        """
        for tier in tiers:
            for i, x in enumerate(self.__tiers):
                f = x[0]
                t = x[1]
                if f == filename and t is tier:
                    self.__tiers.pop(i)
                    self.__cbt.Delete(i)

        if len(self.__tiers) == 0:
            self.Close()

    # -----------------------------------------------------------------------

    def set_selected_tiername(self, filename, tiername, ann_idx):
        """Set the selected tier.

        """
        # Cancel current selected tier and uncheck if only one tier is checked
        self.__selected_tier = -1
        self.__selected_ann = -1
        checked = self.__cbt.GetSelection()
        if len(checked) == 1:
            self.__cbt.SetSelection(checked[0], False)

        for i, x in enumerate(self.__tiers):
            f = x[0]
            t = x[1]
            if f == filename and t.get_name() == tiername:
                is_enabled = True
                if self.__cbt.IsItemEnabled(i) is False:
                    is_enabled = False
                    self.__cbt.EnableItem(i, True)
                self.__cbt.SetSelection(i, True)
                self.__cbt.EnableItem(i, is_enabled)
                self.__selected_tier = i
                self.__selected_ann = ann_idx

    # -----------------------------------------------------------------------

    def get_selected_annotation(self):
        """Return the selected annotation index.

        """
        return self.__selected_ann

    # -----------------------------------------------------------------------
    # Create the UI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the dialog."""
        panel = sppasPanel(self, name="content")
        entry_panel = self.__create_entry_panel(panel)
        tier_panel = self.__create_tier_panel(panel)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(entry_panel, 2, wx.EXPAND)
        sizer.Add(self.__vert_line(panel), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=sppasPanel.fix_size(6))
        sizer.Add(tier_panel, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, border=sppasPanel.fix_size(6))

        panel.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def __create_entry_panel(self, parent):
        # Make the notebook to show each possible type of tag
        notebook = sppasNotebook(parent, name="book_entry")

        # Create and add the pages to the notebook
        page1 = sppasTagStringPanel(notebook)
        notebook.AddPage(page1, " String ")
        page2 = sppasTagIntegerPanel(notebook)
        notebook.AddPage(page2, " Integer ")
        page3 = sppasTagFloatPanel(notebook)
        notebook.AddPage(page3, " Float ")
        page4 = sppasTagBooleanPanel(notebook)
        notebook.AddPage(page4, " Boolean ")

        w, h = page1.GetMinSize()
        notebook.SetMinSize(wx.Size(w, h + (sppasPanel().get_font_height() * 4)))

        return notebook

    # -----------------------------------------------------------------------

    def __create_tier_panel(self, parent):
        cbt = sppasCheckBoxPanel(parent, choices=[], majorDimension=1, style=wx.RA_SPECIFY_COLS, name="checkbox_tiers")
        cbt.SetVGap(sppasPanel.fix_size(2))
        cbt.SetHGap(sppasPanel.fix_size(2))
        return cbt

    # ------------------------------------------------------------------------

    def __vert_line(self, parent):
        """Return a vertical static line."""
        line = sppasStaticLine(parent, orient=wx.LI_VERTICAL)
        line.SetMinSize(wx.Size(1, -1))
        line.SetSize(wx.Size(1, -1))
        line.SetPenStyle(wx.PENSTYLE_SOLID)
        line.SetDepth(1)
        return line

    # ------------------------------------------------------------------------

    @property
    def __cbt(self):
        return self.FindWindow("checkbox_tiers")

    @property
    def __book(self):
        return self.FindWindow("book_entry")

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def notify(self, action, filename, value=None):
        """Notify the parent of an event."""
        wx.LogDebug("{:s} notifies its parent {:s} of action {:s}."
                    "".format(self.GetName(), self.GetParent().GetName(), action))
        evt = SearchViewEvent(action=action, filename=filename, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # Bind all events from our buttons
        self.Bind(wx.EVT_BUTTON, self._process_event)

        # Capture keys
        self.Bind(wx.EVT_CHAR_HOOK, self._process_key_event)

        # Tier selected / Notebook page changed
        self.__cbt.Bind(wx.EVT_CHECKBOX, self._on_tier_checked_event)
        self.__book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_book_page_changed)

    # -----------------------------------------------------------------------

    def _process_event(self, event):
        """Process any kind of events.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        event_name = event_obj.GetName()

        if event_name == "close":
            self.Close()

        elif event_name == "search_forward":
            self.search(forward=True)

        elif event_name == "search_backward":
            self.search(forward=False)

        else:
            event.Skip()

    # -----------------------------------------------------------------------

    def _process_key_event(self, event):
        """Process a key event.

        :param event: (wx.Event)

        """
        key_code = event.GetKeyCode()

        if key_code == wx.WXK_F4 and event.AltDown() and wx.Platform == "__WXMSW__":
            # ALT+F4 under Windows
            self.Close()

        elif event.ControlDown or event.CmdDown():
            if key_code == 87 and wx.Platform != "__WXMSW__":
                # CMD+w under MacOS / Ctrl+w on Linux
                self.Close()

            elif key_code == 71 and not event.ShiftDown():
                # CMD+g under MacOS / Ctrl+g on others
                self.search(forward=True)

            elif key_code == 71 and event.ShiftDown():
                # CMD+SHIFT+G under MacOS / Ctrl+SHIFT+G on others
                self.search(forward=False)

            else:
                event.Skip()

        else:
            event.Skip()

    # -----------------------------------------------------------------------

    def _on_tier_checked_event(self, event):
        """A tier was checked or unchecked.

        :param event: (wx.Event)

        """
        pass

    # -----------------------------------------------------------------------

    def _on_book_page_changed(self, event):
        """The page of the book changed, so does the type of tier to consider."""
        self.update_checkable_tiers()

    # -----------------------------------------------------------------------

    def update_checkable_tiers(self):
        """Enable only the tiers matching the type of the page of the book."""
        page_idx = self.__book.GetSelection()
        page = self.__book.GetPage(page_idx)
        for i in range(len(self.__tiers)):
            f, t = self.__tiers[i]
            if isinstance(page, sppasTagStringPanel) and t.is_string():
                self.__cbt.EnableItem(i, enable=True)
            elif isinstance(page, sppasTagIntegerPanel) and t.is_int():
                self.__cbt.EnableItem(i, enable=True)
            elif isinstance(page, sppasTagFloatPanel) and t.is_float():
                self.__cbt.EnableItem(i, enable=True)
            elif isinstance(page, sppasTagBooleanPanel) and t.is_bool():
                self.__cbt.EnableItem(i, enable=True)
            else:
                self.__cbt.EnableItem(i, enable=False)

    # -----------------------------------------------------------------------

    def search(self, forward=True):
        """Search for tags matching a fixed criteria in given tiers."""
        checked = self.__cbt.GetSelection()
        if len(checked) == 0:
            wx.LogInfo("At least one tier must be checked in order to search for tags...")
            return

        # Data the user entered and/or checked
        page_idx = self.__book.GetSelection()
        data = self.__book.GetPage(page_idx).get_data()
        tag_functions = sppasBaseFilters.fix_functions(self.__comparator, **{data[1]: data[2][0]})

        # Search in the checked tiers
        matching_ann_idx = None
        matching_tier_idx = -1
        matching_time = None
        tier = self.__tiers[self.__selected_tier][1]
        search_time = self.__get_timepos(tier[self.__selected_ann], forward)
        direction = 1
        if forward is False:
            direction = -1
        for tier_idx in self.__cbt.GetSelection():
            tier = self.__tiers[tier_idx][1]
            # index of the 1st annotation to start to search
            start_idx = tier.near(search_time, direction)

            if forward is True:
                for i in range(start_idx, len(tier)):
                    tp = self.__get_timepos(tier[i], forward=False)
                    if matching_ann_idx is not None and matching_time < tp:
                        # a match was already found before the current time
                        break
                    is_matching = self.__matching(tier[i], tag_functions)
                    if is_matching is True:
                        matching_tier_idx = tier_idx
                        matching_ann_idx = i
                        matching_time = self.__get_timepos(tier[i], forward=False)
                        break
            else:
                for i in reversed(range(self.__selected_ann)):
                    tp = self.__get_timepos(tier[i], forward=True)
                    if matching_ann_idx is not None and matching_time > tp:
                        # a match was already found after the current time
                        break
                    is_matching = self.__matching(tier[i], tag_functions)
                    if is_matching is True:
                        matching_tier_idx = tier_idx
                        matching_ann_idx = i
                        matching_time = self.__get_timepos(tier[i], forward=True)
                        break

        if matching_ann_idx is not None:
            self.__selected_tier = matching_tier_idx
            self.__selected_ann = matching_ann_idx
            self.notify(action="tier_selected",
                        filename=self.__tiers[self.__selected_tier][0],
                        value=self.__tiers[self.__selected_tier][1].get_name())

    # -----------------------------------------------------------------------

    def __matching(self, ann, tag_functions):
        for label in ann.get_labels():
            is_matching = label.match(tag_functions)
            if is_matching is True:
                return True
        return False

    # -----------------------------------------------------------------------

    def __get_timepos(self, ann, forward):
        """Return a time value."""
        if self.__selected_tier == -1:
            return 0.
        if self.__selected_ann == -1:
            return 0.

        if forward is True:
            loc = ann.get_highest_localization()
            if loc.is_float() is False:
                return 0.
            radius = 0.
            if loc.get_radius() is not None:
                radius = loc.get_radius()
            return loc.get_midpoint() + radius
        else:
            loc = ann.get_lowest_localization()
            if loc.is_float() is False:
                return 0.
            radius = 0.
            if loc.get_radius() is not None:
                radius = loc.get_radius()
            return loc.get_midpoint() - radius

# ---------------------------------------------------------------------------


class SearchActionsPanel(sppasPanel):
    """Create my own panel with some action buttons.

    """
    def __init__(self, parent):

        super(SearchActionsPanel, self).__init__(
            parent=parent,
            style=wx.WANTS_CHARS | wx.TAB_TRAVERSAL | wx.NO_BORDER,
            name="pnl_actions")

        settings = wx.GetApp().settings

        # Create the action panel and sizer
        self.SetMinSize(wx.Size(-1, settings.action_height))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        close_btn = self._create_button(MSG_ACTION_CLOSE, "close")
        forward_btn = self._create_button(MSG_ACTION_FORWARD, "search_forward")
        backward_btn = self._create_button(MSG_ACTION_BACKWARD, "search_backward")

        sizer.Add(backward_btn, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(forward_btn, 1, wx.ALL | wx.EXPAND, 0)
        sizer.Add(self.VertLine(), 0, wx.ALL | wx.EXPAND, 0)
        sizer.Add(close_btn, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def _create_button(self, text, icon):
        btn = BitmapTextButton(self, label=text, name=icon)

        # Get the font height for the header
        h = self.get_font_height()

        btn.SetLabelPosition(wx.RIGHT)
        btn.SetFocusStyle(wx.PENSTYLE_SOLID)
        btn.SetFocusWidth(1)
        btn.SetFocusColour(wx.Colour(128, 128, 128, 128))
        # btn.SetSpacing(sppasPanel.fix_size(h//2))
        btn.SetMinSize(wx.Size(h*10, h*2))
        btn.Bind(sb.EVT_WINDOW_FOCUSED, self._on_btn_focused)
        btn.Bind(sb.EVT_WINDOW_SELECTED, self._on_btn_selected)

        return btn

    # -----------------------------------------------------------------------

    def _on_btn_selected(self, event):
        pass

    # -----------------------------------------------------------------------

    def _on_btn_focused(self, event):
        win = event.GetEventObject()
        is_focused = event.GetFocused()
        if is_focused is True:
            win.SetFont(win.GetFont().MakeLarger())
        else:
            win.SetFont(win.GetFont().MakeSmaller())

    # ------------------------------------------------------------------------

    def VertLine(self):
        """Return a vertical static line."""
        line = sppasStaticLine(self, orient=wx.LI_VERTICAL)
        line.SetMinSize(wx.Size(3, -1))
        line.SetSize(wx.Size(3, -1))
        line.SetPenStyle(wx.PENSTYLE_SOLID)
        line.SetDepth(1)
        return line


# ----------------------------------------------------------------------------
# Panels to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Panel):
    TEST_FILES = (
        os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra"),
        os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-momel.PitchTier"),
    )

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            name="sppasSearchFrame")

        btn1 = wx.Button(self, label="Open frame", pos=(10, 10), size=(128, 64))
        self.Bind(wx.EVT_BUTTON, self._on_open_search, btn1)

    # -----------------------------------------------------------------------

    def _on_open_search(self, event):
        search = sppasSearchTagDialog(self)

        all_trs = list()
        for filename in TestPanel.TEST_FILES:
            parser = sppasTrsRW(filename)
            trs = parser.read()
            search.add_tiers(filename, [t for t in trs])
            all_trs.append(trs)

        search.set_selected_tiername(TestPanel.TEST_FILES[0], all_trs[0][1].get_name(), 0)
        search.Show()

