"""
:filename: sppas.src.ui.phoenix.page_editor.timeline.trsvista.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Timeline view of a transcription

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

from sppas.src.config import paths
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription

from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.panels import sppasScrolledPanel
from sppas.src.ui.phoenix.windows.popup import PopupCheckBox

from ..datactrls.layerctrl import sppasTierWindow
from ..datactrls.layerctrl import EVT_TIER

# ---------------------------------------------------------------------------


TrsEvent, EVT_TRS = wx.lib.newevent.NewEvent()
TrsCommandEvent, EVT_TRS_COMMAND = wx.lib.newevent.NewCommandEvent()

# ---------------------------------------------------------------------------


class TranscriptionVista(sppasPanel):
    """Display a transcription in a timeline view.

    Only one tier must be selected at a time and only one annotation can be
    selected in the selected tier.

    Event emitted by this class is TRS_EVENT with:

        - action="select_tier", value=name of the tier to be selected

    """

    def __init__(self, parent, name="trsvista_panel"):
        super(TranscriptionVista, self).__init__(parent, name=name)
        # The sppasTranscription() to be represented
        self.__trs = None

        # Create the view content
        self._create_content()

        # Associate a popup to display the filename
        self._check_popup = PopupCheckBox(self.GetTopLevelParent(), choices=list())
        self._check_popup.Bind(wx.EVT_MOUSE_EVENTS, self._check_popup_mouse_event)

        # A menu is shown on right-click to check the tiers to be displayed
        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        # Events related to the embedded transcription
        self.Bind(EVT_TIER, self.__process_tier_event)

    # -----------------------------------------------------------------------

    def __process_tier_event(self, event):
        """Process an event from the embedded tier.

        This is a solution to convert the EVT_TIER received from a
        sppasTierWindow into an EVT_TRS.

        :param event: (wx.Event)

        """
        self.notify(action=event.action, value=event.value)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override to keep the tier height proportional."""
        wx.Panel.SetFont(self, font)
        for tier_ctrl in self.GetChildren():
            tier_ctrl.SetFont(font)
            tier_ctrl.SetMinSize(wx.Size(-1, self.get_font_height() * 2))
        self.Layout()

    # -----------------------------------------------------------------------

    def set_transcription(self, transcription):
        """Fix the transcription object if it wasn't done when init.

        """
        if self.__trs is not None:
            raise Exception("A sppasTranscription is already defined.")

        if isinstance(transcription, sppasTranscription):
            self.__trs = transcription
            for tier in self.__trs:
                self._add_tier_to_panel(tier)

            self.SetMinSize(wx.Size(-1, len(self.__trs) * self.get_font_height() * 2))

    # -----------------------------------------------------------------------

    def write_transcription(self, parser):
        """Write the transcription object with the given parser.

        :param parser: (sppasRW)

        """
        parser.write(self.__trs)

    # -----------------------------------------------------------------------

    def get_duration(self):
        """Return the duration of the transcription."""
        if self.__trs is not None:
            max_point = self.__trs.get_max_loc()
            if max_point is not None:
                midpoint = max_point.get_midpoint()
                radius = max_point.get_radius()
                if radius is None:
                    return midpoint
                else:
                    return midpoint + radius

        return 0.

    # -----------------------------------------------------------------------

    def set_visible_period(self, start, end):
        """Period to display (in seconds)."""
        for child in self.GetChildren():
            changed = child.set_visible_period(start, end)
            if changed is True and child.IsShown():
                child.Refresh()

    # -----------------------------------------------------------------------

    def set_selection_period(self, start, end):
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def get_selected_tiername(self):
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_tiername()
        return None

    # -----------------------------------------------------------------------

    def set_selected_tiername(self, tier_name=None):
        """Set the selected tier.

        :param tier_name: (str)

        """
        if self.__trs is None:
            return

        if tier_name is not None:
            assert tier_name in [t.get_name() for t in self.__trs]

        for child in self.GetChildren():
            if child.is_selected() is True:
                child.set_selected(False)
                child.Refresh()
            if child.get_tiername() == tier_name:
                child.set_selected(True)
                child.Refresh()

    # -----------------------------------------------------------------------

    def get_tier_list(self):
        """Return the list of tiers."""
        if self.__trs is not None:
            return self.__trs.get_tier_list()
        return list()

    # -----------------------------------------------------------------------

    def get_selected_localization(self):
        """Return begin and end time value (float) rounded to milliseconds."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_selected_localization()

        return 0., 0.

    # -----------------------------------------------------------------------

    def get_selected_ann(self):
        """Return the index of the currently selected annotation or -1."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                return child.get_selected_ann()

        return -1

    # -----------------------------------------------------------------------

    def set_selected_ann(self, idx):
        """An annotation was selected."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.set_selected_ann(idx)

    # -----------------------------------------------------------------------

    def update_ann(self, idx):
        """An annotation was modified."""
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.update_ann(idx)

    # -----------------------------------------------------------------------

    def delete_ann(self, idx):
        """An annotation was deleted.

        If the idx was the selected ann, there's no remaining selected
        annotation after delete.

        """
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.delete_ann(idx)

    # -----------------------------------------------------------------------

    def create_ann(self, idx):
        """An annotation was created. """
        for child in self.GetChildren():
            if child.is_selected() is True:
                child.update_ann(idx)

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def show_tier_infos(self, value, tiername=None):
        """Show information about a tier instead or the annotations.

        :param value: (bool) True to show the information, False for the annotations.
        :param tiername: (str) Name of a tier or None for all tiers

        """
        if self.__trs is None:
            return
        for child in self.GetChildren():
            if tiername is None or tiername == child.get_tiername():
                child.show_infos(value)
                child.Refresh()

    # -----------------------------------------------------------------------

    def _create_content(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

    # -----------------------------------------------------------------------

    def _add_tier_to_panel(self, tier):
        tier_ctrl = sppasTierWindow(self, tier=tier)
        tier_ctrl.SetBackgroundColour(self.GetBackgroundColour())
        tier_ctrl.SetForegroundColour(self.GetForegroundColour())
        tier_ctrl.SetMinSize(wx.Size(-1, self.get_font_height() * 2))
        tier_ctrl.Bind(wx.EVT_COMMAND_LEFT_CLICK, self._process_tier_selected)
        i = self._check_popup.checkbox.Append(tier.get_name())
        self._check_popup.checkbox.SetSelection(i)

        self.GetSizer().Add(tier_ctrl, 0, wx.EXPAND, 0)

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def notify(self, action, value=None):
        """Send a EVT_TRS event to the listener (if any)."""
        evt = TrsEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _process_tier_selected(self, event):
        """Process a click on a tier or an annotation of a tier.

        :param event: (wx.Event)

        """
        # Which tier was clicked?
        tierctrl_click = event.GetEventObject()

        # Do not accept that a tier decides by its own to deselect
        if tierctrl_click.is_selected() is False:
            tierctrl_click.set_selected(True)

        else:
            # Update selection: disable a previously selected tier
            for child in self.GetChildren():
                if child is not tierctrl_click and child.is_selected():
                    child.set_selected(False)
                    child.Refresh()

        self.notify(action="tier_selected", value=tierctrl_click.get_tiername())

    # -----------------------------------------------------------------------

    def _on_context_menu(self, event):
        """Show menu to check the tiers to be displayed.

        """
        mx, my = wx.GetMousePosition()
        # we need to put the mouse inside the popup
        cx = mx - sppasPanel.fix_size(10)

        # The parent of the popup is the top-level window so does it's position
        w, h = self._check_popup.checkbox.DoGetBestSize()
        self._check_popup.SetPosition(wx.Point(cx, my - (h // 2)))
        self._check_popup.SetSize(wx.Size(sppasPanel.fix_size(150), h))

        # Show the popup window
        self._check_popup.Layout()
        self._check_popup.Show()
        self._check_popup.SetFocus()
        self._check_popup.Raise()

    # ------------------------------------------------------------------------

    def _check_popup_mouse_event(self, event):
        """Mouse action on the menu to check the tiers to be displayed.

        """
        if event.Leaving():
            # Mouse went out, don't show the menu anymore
            self._check_popup.Hide()
            # Get the name of the checked tiers in the popup check box
            checked_tier_idx = self._check_popup.checkbox.GetSelection()
            wx.LogDebug("Checked choices: {}".format(checked_tier_idx))
            # Show/Hide tiers
            nb = 0
            for i, child in enumerate(self.GetChildren()):
                if i in checked_tier_idx and self._check_popup.checkbox.IsItemEnabled(i):
                    nb += 1
                    child.Show()
                else:
                    child.Hide()
            # Resize
            self.SetMinSize(wx.Size(-1, nb * self.get_font_height() * 2))
            self.notify(action="size")

# ---------------------------------------------------------------------------


class TestPanel(sppasScrolledPanel):
    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="TrsVista Panel")
        f1 = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P9-palign.xra")
        trs1 = sppasTrsRW(f1).read()
        p1 = TranscriptionVista(self, name="p1")
        p1.SetPosition(wx.Point(10, 10))
        p1.SetSize(wx.Size(600, 80))
        p1.set_transcription(trs1)
        return
