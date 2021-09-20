# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_analyze.datalist.trsrisepanel.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Display objects embedded into a sppasTranscription (see anndata).

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

import re
import os
import wx
import wx.lib.scrolledpanel

from sppas.src.config import paths
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata.aio.basetrsio import sppasBaseIO
from sppas.src.anndata.anndataexc import TrsAddError
from sppas.src.analysis.tierfilters import SingleFilterTier
from sppas.src.analysis.tierfilters import RelationFilterTier

from sppas.src.ui.phoenix.views import MetaDataEdit

from ..basefilelist import sppasFileSummaryPanel

from .baseobjlist import EVT_ITEM_CLICKED
from .tierslist import TiersListCtrl
from .mediaslist import MediaListCtrl
from .vocabslist import CtrlVocabListCtrl

# ---------------------------------------------------------------------------


class TrsSummaryPanel(sppasFileSummaryPanel):
    """A panel to display the summary of an annotated file.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    Can not be constructed if the file is not supported and/or if an error
    occurred when opening or reading.

    """

    def __init__(self, parent, filename, name="trs_panel"):
        if os.path.exists(filename) is True:
            try:
                # Before creating the trs, check if the file is supported.
                parser = sppasTrsRW(filename)
                self._trs = parser.read()
                dirty = False
            except TypeError:
                self.Destroy()
                raise
        else:
            self._trs = sppasTranscription("New Document")
            dirty = True

        super(TrsSummaryPanel, self).__init__(parent, filename, name)
        self._dirty = dirty
        self.__set_metadata()
        self.__set_selected(self._trs.get_meta("private_selected"))
        self.Bind(wx.EVT_BUTTON, self.__process_tool_event)

        self.Collapse(self.str_to_bool(self._trs.get_meta("private_collapsed")))
        self._hicolor = wx.Colour(200, 200, 180)
        self._rgb1 = (245, 240, 160)
        self._rgb2 = (255, 255, 205)
        self.SetRandomColours()

    # -----------------------------------------------------------------------

    def SetHighLightColor(self, color):
        """Set a color to highlight the filename if selected."""
        self._hicolor = color
        if self._trs.get_meta("private_selected", "False") == "True":
            self.GetToolsPane().SetBackgroundColour(self._hicolor)
        else:
            self.GetToolsPane().SetBackgroundColour(self._tools_bg_color)
        self.Refresh()

    # -----------------------------------------------------------------------

    def is_selected(self):
        """Return True is this file is selected."""
        return self.str_to_bool(self._trs.get_meta("private_selected", "False"))

    # ------------------------------------------------------------------------

    def get_object_in_trs(self, identifier):
        """Return the class object matching the given identifier.

        :param identifier: (str)
        :return: (sppasTier, sppasCtrlVocab, sppasMedia)

        """
        obj = self._trs.get_tier_from_id(identifier)
        if obj is not None:
            return obj

        obj = self._trs.get_media_from_id(identifier)
        if obj is not None:
            return obj

        obj = self._trs.get_ctrl_vocab_from_id(identifier)
        if obj is not None:
            return obj

        return None

    # -----------------------------------------------------------------------

    def get_tier_list(self):
        """Return the list of all tiers."""
        return self._trs.get_tier_list()

    # -----------------------------------------------------------------------

    def get_tiernames(self):
        """Return the list of all tier names."""
        return [tier.get_name() for tier in self._trs.get_tier_list()]

    # -----------------------------------------------------------------------

    def get_checked_tier(self):
        """Return the list of checked tiers."""
        checked = list()
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                checked.append(tier)

        return checked

    # -----------------------------------------------------------------------

    def get_nb_checked_tier(self):
        """Return the number of checked tiers."""
        nb = 0
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                nb += 1
                wx.LogDebug("Tier {:s} is checked.".format(tier.get_name()))
            else:
                wx.LogDebug("Tier {:s} is not checked.".format(tier.get_name()))

        return nb

    # -----------------------------------------------------------------------

    def check_tier(self, name):
        """Check tier matching the given regexp. Uncheck the others."""
        panel = self.FindWindow("tiers_listctrl")
        for tier in self._trs.get_tier_list():
            is_matching = re.match(name, tier.get_name())
            if is_matching is not None:
                if tier.get_meta("private_checked") == "False":
                    tier.set_meta("private_checked", "True")
                    panel.change_state(tier.get_id(), "True")
                    self._dirty = True
            else:
                if tier.get_meta("private_checked") == "True":
                    tier.set_meta("private_checked", "False")
                    panel.change_state(tier.get_id(), "False")
                    self._dirty = True

    # -----------------------------------------------------------------------

    def uncheck_tier(self):
        """Uncheck tiers."""
        panel = self.FindWindow("tiers_listctrl")
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                tier.set_meta("private_checked", "False")
                panel.change_state(tier.get_id(), "False")
                self._dirty = True

    # -----------------------------------------------------------------------

    def rename_tier(self, new_name):
        """Rename the checked tier.

        :param new_name: (str)

        """
        if len(new_name) == 0:
            new_name = None
        panel = self.FindWindow("tiers_listctrl")
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                old_name = tier.get_name()
                if old_name != new_name:
                    tier.set_name(new_name)
                    new_name = tier.get_name()
                    panel.update_item(tier)
                    wx.LogMessage("Tier {:s} renamed to {:s}"
                                  "".format(old_name, new_name))
                    self._dirty = True

    # -----------------------------------------------------------------------

    def delete_tier(self, tier_id=None):
        """Delete all checked tiers or the tier which name is exactly matching.

        :param tier_id: (str or None)

        """
        panel = self.FindWindow("tiers_listctrl")
        if tier_id is not None:
            tier = self._trs.find_id(tier_id)
            if tier is not None:
                panel.remove(tier.get_id())
                i = self._trs.get_tier_index_id(tier.get_id())
                self._trs.pop(i)

        else:
            i = len(self._trs)
            for tier in reversed(self._trs.get_tier_list()):
                i -= 1
                if tier.get_meta("private_checked") == "True":
                    panel.remove(tier.get_id())
                    self._trs.pop(i)

        self.Layout()

    # -----------------------------------------------------------------------

    def cut_tier(self):
        """Remove checked tiers of the transcription and return them.

        :return: (list of sppasTier)

        """
        clipboard = list()
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                # Copy the tier to the clipboard
                new_tier = tier.copy()
                clipboard.append(new_tier)

        if len(clipboard) > 0:
            self.delete_tier()
            self._dirty = True

        return clipboard

    # -----------------------------------------------------------------------

    def copy_tier(self):
        """Copy checked tiers to the clipboard.

        :return: (list of sppasTier)

        """
        clipboard = list()
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                # Copy the tier to the clipboard
                new_tier = tier.copy()

                # Invalidate its links to other data of its transcription
                new_tier.set_ctrl_vocab(None)
                new_tier.set_media(None)
                new_tier.set_parent(None)

                clipboard.append(new_tier)

        return clipboard

    # -----------------------------------------------------------------------

    def paste_tier(self, clipboard):
        """Paste the clipboard tier(s) to the current page.

        :param clipboard: (list of tiers, or None)
        :return: (int) Number of tiers added

        """
        added = 0
        panel = self.FindWindow("tiers_listctrl")

        # Append clipboard tiers to the transcription
        for tier in clipboard:
            copied_tier = tier.copy()
            # copied_tier.gen_id()
            try:
                self._trs.append(copied_tier)
                # The tier comes from another Transcription... must update infos.
                if not (copied_tier.get_parent() is self._trs):
                    copied_tier.set_parent(self._trs)
                panel.add(copied_tier)
                added += 1
                self._dirty = True
            except TrsAddError as e:
                wx.LogError("Paste tier error: {:s}".format(str(e)))

        return added

    # -----------------------------------------------------------------------

    def duplicate_tier(self):
        """Duplicate the checked tiers."""
        panel = self.FindWindow("tiers_listctrl")

        nb = 0
        for tier in reversed(self._trs.get_tier_list()):
            if tier.get_meta("private_checked") == "True":
                new_tier = tier.copy()
                new_tier.gen_id()
                new_tier.set_meta("private_checked", "False")
                new_tier.set_meta("tier_was_duplicated_from_id", tier.get_meta('id'))
                new_tier.set_meta("tier_was_duplicated_from_name", tier.get_name())
                self._trs.append(new_tier)
                panel.add(new_tier)
                nb += 1
                self._dirty = True

        return nb

    # -----------------------------------------------------------------------

    def move_up_tier(self):
        """Move up the checked tiers (except for the first one)."""
        panel = self.FindWindow("tiers_listctrl")

        for i, tier in enumerate(self._trs.get_tier_list()):
            if tier.get_meta("private_checked") == "True" and i > 0:
                # move up into the transcription
                self._trs.set_tier_index_id(tier.get_id(), i - 1)
                wx.LogDebug("Tier {:s} moved to index {:d}".format(tier.get_name(), i-1))

                # move up into the panel
                panel.remove(tier.get_id())
                panel.add(tier, i-1)
                self._dirty = True

    # ------------------------------------------------------------------------

    def move_down_tier(self):
        """Move down the checked tiers (except for the last one)."""
        panel = self.FindWindow("tiers_listctrl")

        i = len(self._trs.get_tier_list())
        for tier in reversed(self._trs.get_tier_list()):
            i = i - 1
            if tier.get_meta("private_checked") == "True" and (i+1) < len(tier):
                # move down into the transcription
                self._trs.set_tier_index_id(tier.get_id(), i + 1)
                wx.LogDebug("Tier {:s} moved to index {:d}".format(tier.get_name(), i+1))

                # move down into the panel
                panel.remove(tier.get_id())
                panel.add(tier, i+1)
                self._dirty = True

    # -----------------------------------------------------------------------

    def radius(self, r, tier_id=None):
        """Fix a new radius value to the given tier or the checked tiers.

        :param r: (int or float) Value of the vagueness
        :param tier_id: (str or None)

        """
        if tier_id is not None:
            tier = self._trs.find_id(tier_id)
            if tier is not None:
                tier.set_radius(r)
        else:
            for tier in self._trs.get_tier_list():
                p = tier.get_first_point()
                if p is None:
                    continue
                if tier.get_meta("private_checked") == "True":
                    try:
                        radius = r
                        if p.is_float() is True:
                            radius = float(r)
                        tier.set_radius(radius)
                        self._dirty = True
                        wx.LogMessage(
                            "Radius set to tier {:s} of file {:s}: {:s}"
                            "".format(tier.get_name(), self._filename, str(r)))
                    except Exception as e:
                        wx.LogError(
                            "Radius not set to tier {:s} of file {:s}: {:s}"
                            "".format(tier.get_name(), self._filename, str(e)))

    # -----------------------------------------------------------------------

    def single_filter(self, filters,
                      match_all=False,
                      annot_format=False,
                      out_tiername="Filtered"):
        """Apply filters on the checked tiers.

        :param filters: (list of tuples)
        :param match_all: (bool)
        :param annot_format: (bool) Replace the label by the name of the filter
        :param out_tiername: (str)

        """
        panel = self.FindWindow("tiers_listctrl")
        nb = 0

        ft = SingleFilterTier(filters, annot_format, match_all)
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                new_tier = ft.filter_tier(tier, out_tiername)
                if new_tier is not None:
                    self._trs.append(new_tier)
                    self._dirty = True
                    panel.add(new_tier, len(self._trs))
                    nb += 1

        return nb

    # -----------------------------------------------------------------------

    def relation_filter(self, filters,
                        y_tiername,
                        annot_format=False,
                        fit_option=False,
                        out_tiername="Filtered"):
        """Apply 'rel' filters on the checked tiers.

        :param filters: (list)
        :param y_tiername: (str) Name of the tier to be in relation with.
        :param annot_format: (bool) Replace the label by the name of the filter
        :param out_tiername: (str)

        """
        panel = self.FindWindow("tiers_listctrl")
        if self.get_nb_checked_tier() == 0:
            return 0
        y_tier = self._trs.find(y_tiername)
        if y_tier is None:
            wx.LogWarning("No tier with name {:s} in {:s}."
                          "".format(y_tiername, self._filename))
            return 0

        nb = 0
        ft = RelationFilterTier(filters, annot_format, fit=fit_option)
        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked") == "True":
                new_tier = ft.filter_tier(tier, y_tier, out_tiername)
                if new_tier is not None:
                    self._trs.append(new_tier)
                    self._dirty = True
                    panel.add(new_tier, len(self._trs))
                    nb += 1

        return nb

    # -----------------------------------------------------------------------
    # Override from the parent
    # -----------------------------------------------------------------------

    def save(self, filename=None):
        """Save the displayed transcription into a file.

        :param filename: (str) To be used to "save as..."

        """
        parser = None
        if filename is None and self._dirty is True:
            # the writer will increase the file version
            parser = sppasTrsRW(self._filename)
            self._dirty = False
        if filename is not None:
            parser = sppasTrsRW(filename)

        if parser is not None:
            parser.write(self._trs)
            return True
        return False

    # -----------------------------------------------------------------------

    def _create_content(self):
        """Override. Create the content of the panel."""
        self.AddButton("tags", direction=1)
        self.AddButton("select", direction=1)
        self.AddButton("save", direction=1)
        self.AddButton("close", direction=1)

        self._create_child_panel()

    # ------------------------------------------------------------------------

    def _create_child_panel(self):
        """Override. Create the child panel."""
        child_panel = self.GetPane()

        # Display the list of tiers
        tier_ctrl = TiersListCtrl(child_panel, self._trs.get_tier_list(), name="tiers_listctrl")

        # Display the list of medias
        media_ctrl = MediaListCtrl(child_panel, self._trs.get_media_list(), name="media_listctrl")
        if isinstance(self._trs, sppasBaseIO) is False:
            media_ctrl.Hide()
        else:
            if self._trs.media_support() is False:
                media_ctrl.Hide()

        # Display the list of controlled vocabulaties
        vocab_ctrl = CtrlVocabListCtrl(child_panel, self._trs.get_ctrl_vocab_list(), name="vocab_listctrl")
        if isinstance(self._trs, sppasBaseIO) is False:
            vocab_ctrl.Hide()
        else:
            if self._trs.ctrl_vocab_support() is False:
                vocab_ctrl.Hide()

        # todo: display the list of hierarchy links
        # hy_ctrl = self.__create_hyctrl()

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(tier_ctrl, 0, wx.EXPAND | wx.TOP, sppasFileSummaryPanel.fix_size(8))
        s.Add(media_ctrl, 0, wx.EXPAND)
        s.Add(vocab_ctrl, 0, wx.EXPAND)
        # s.Add(hy_ctrl, 0, wx.EXPAND)

        child_panel.SetMinSize(wx.Size(-1, 24))
        child_panel.SetSizer(s)

        # The user clicked an item
        child_panel.Bind(EVT_ITEM_CLICKED, self._process_item_clicked)

    # ------------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _process_item_clicked(self, event):
        """Process an action event: an item was clicked.

        The sender of the event is a CheckListCtrl.

        :param event: (wx.Event)

        """
        object_id = event.id
        obj = self.get_object_in_trs(object_id)

        # change state of the item
        current_state = obj.get_meta("private_checked")
        new_state = "False"
        if current_state == "False":
            new_state = "True"
        obj.set_meta("private_checked", new_state)
        self._dirty = True

        # update the corresponding panel(s)
        panel = event.GetEventObject()
        panel.change_state(object_id, new_state)

    # -----------------------------------------------------------------------

    def __process_tool_event(self, event):
        """Process an event from a button.

        :param event: (wx.Event)

        """
        event_obj = event.GetEventObject()
        name = event_obj.GetName()

        if name == "save":
            self.notify(action="save")

        elif name == "close":
            self.notify(action="close")

        elif name == "select":
            self.__set_selected()

        elif name == "tags":
            MetaDataEdit(self, [self._trs])

    # ------------------------------------------------------------------------

    @staticmethod
    def str_to_bool(value):
        if value.lower() == "true":
            return True
        try:
            if value.isdigit() and int(value) > 0:
                return True
        except AttributeError:
            pass
        return False

    # -----------------------------------------------------------------------

    def update(self):
        """Update the controls to match the data."""
        panel = self.FindWindow("tiers_listctrl")
        for i, tier in enumerate(self._trs.get_tier_list()):
            #self.__update_tier(tier, i)
            panel.add_item(tier)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __set_selected(self, value=None):
        """Force to set the given selected value or reverse the existing one."""
        # Old value can be unknown (not already set)
        old_value = self._trs.get_meta("private_selected", None)
        if old_value is None:
            self._trs.set_meta("private_selected", "False")

        # Given new value is None. We switch the old one.
        if value is None:
            if self._trs.get_meta("private_selected") == "False":
                value = "True"
            else:
                value = "False"

        if value != self._trs.get_meta("private_selected", "x"):
            self._trs.set_meta("private_selected", value)
            self._dirty = True

            if self._trs.get_meta("private_selected", "False") == "True":
                self.GetToolsPane().SetBackgroundColour(self._hicolor)
            else:
                self.GetToolsPane().SetBackgroundColour(self._tools_bg_color)

            self.Refresh()

    # ------------------------------------------------------------------------

    def __set_metadata(self):
        """Set metadata to the object about checked or selected items."""
        if self._trs.get_meta("private_selected", None) is None:
            self._trs.set_meta("private_selected", "False")

        if self._trs.get_meta("private_checked", None) is None:
            self._trs.set_meta("private_checked", "False")
        if self._trs.get_meta("private_collapsed", None) is None:
            self._trs.set_meta("private_collapsed", "False")

        for tier in self._trs.get_tier_list():
            if tier.get_meta("private_checked", None) is None:
                tier.set_meta("private_checked", "False")

        for media in self._trs.get_media_list():
            if media.get_meta("private_checked", None) is None:
                media.set_meta("private_checked", "False")

        for vocab in self._trs.get_ctrl_vocab_list():
            if vocab.get_meta("private_checked", None) is None:
                vocab.set_meta("private_checked", "False")

# ----------------------------------------------------------------------------
# Panel to test the class
# ----------------------------------------------------------------------------


class TestPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.ALWAYS_SHOW_SB | wx.HSCROLL | wx.VSCROLL,
            name="Test Transcription Summary Panel")

        f1 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra")
        f2 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-salign.xra")
        f3 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P9-palign.xra")
        p1 = TrsSummaryPanel(self, f1)
        p2 = TrsSummaryPanel(self, f2)
        p3 = TrsSummaryPanel(self, f3)

        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapseChanged, p1)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapseChanged, p2)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapseChanged, p3)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(p1, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(p2, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(p3, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer)
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.SetAutoLayout(True)
        self.Layout()

    def OnCollapseChanged(self, evt=None):
        panel = evt.GetEventObject()
        panel.SetFocus()
        self.Layout()

