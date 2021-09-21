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

    ui.phoenix.page_edit.baseview_risepanel.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A base class for any object that displays the content of a file in a
    timeline.

"""

import wx
import os
import random

from sppas.src.config import paths

from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.panels import sppasBaseRisePanel
from sppas.src.ui.phoenix.windows.buttons import BitmapButton
from sppas.src.ui.phoenix.windows.buttons import ToggleButton
from sppas.src.ui.phoenix.windows.popup import PopupLabel

from .timedatatype import TimelineType
from .timeevents import TimelineViewEvent

# ---------------------------------------------------------------------------


class sppasTimelineCollapsiblePanel(sppasBaseRisePanel):
    """A vert- oriented rise panel with an horiz- toolbar when collapsed.

    """
    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name="collapsible_panel"):
        """Create a sppasHorizVertRisePanel.

        :param parent: (wx.Window) Parent window must NOT be none
        :param id: (int) window identifier or -1
        :param label: (string) Label of the button
        :param pos: (wx.Pos) the control position
        :param size: (wx.Size) the control size
        :param style: (int) the underlying window style
        :param name: (str) the widget name.

        The parent can Bind the wx.EVT_COLLAPSIBLEPANE_CHANGED.

        """
        self._collapsed_tools_panel = None
        super(sppasTimelineCollapsiblePanel, self).__init__(
            parent, id, label, pos, size, style, name=name)

        # Create a toolbar and show it only when collapsed.
        self._collapsed_tools_panel = sppasPanel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label_btn = self._create_tool_button("slashdot")
        label_btn.Bind(wx.EVT_BUTTON, self._process_label_event)
        sizer.Add(label_btn, 0, wx.FIXED_MINSIZE | wx.TOP, 1)
        self._collapsed_tools_panel.SetSizer(sizer)
        self._collapsed_tools_panel.Show(False)
        self.Layout()

    # -----------------------------------------------------------------------

    def EnableButton(self, icon, value):
        """Enable or disable a button of the tools panel.

        :param icon: (str) Name of the .png file of the icon
        :param value: (bool)

        """
        btn = self._collapsed_tools_panel.FindWindow(icon)
        if btn is None or btn == self._btn:
            return
        btn.Enable(value)

    # -----------------------------------------------------------------------

    def FindButton(self, icon):
        """Return the button with the given icon name or None."""
        for child in self._collapsed_tools_panel.GetChildren():
            if child.GetName() == icon and child != self._btn:
                return child
        return None

    # -----------------------------------------------------------------------

    def AddButton(self, icon):
        """Append a button into the toolbar.

        :param icon: (str) Name of the .png file of the icon or None

        """
        btn = self._create_tool_button(icon, label=None)
        self._collapsed_tools_panel.GetSizer().Add(btn, 0, wx.TOP, 1)

        return btn

    # -----------------------------------------------------------------------

    def GetButtonWidth(self):
        """Return the width of the buttons in the toolbar."""
        return int(float(self.get_font_height()) * 1.8)

    # -----------------------------------------------------------------------

    def SetInitialSize(self, size=None):
        """Calculate and set a good size.

        :param size: an instance of wx.Size.

        """
        tb_w, tb_h = self._tools_panel.GetMinSize()
        min_w = tb_w
        min_h = tb_h
        self.SetMinSize(wx.Size(min_w, min_h))

        if size is None:
            size = wx.DefaultSize
        wx.Window.SetInitialSize(self, size)

    SetBestSize = SetInitialSize

    # -----------------------------------------------------------------------

    def DoGetBestSize(self):
        """Get the size which best suits the window."""
        if self.IsExpanded() is True:
            tb_w, tb_h = self._tools_panel.DoGetBestSize()
        else:
            tb_w, tb_h = self._tools_panel.GetMinSize()

        best_w = tb_w
        best_h = tb_h

        if self.IsExpanded() and self._child_panel:
            child_w, child_h = self._child_panel.GetBestSize()
            best_w = tb_w + child_w
            best_h = max(child_h, tb_h)

        return wx.Size(best_w, best_h)

    # -----------------------------------------------------------------------

    def Layout(self):
        """Do the layout."""
        # we need to complete the creation first
        if not self._tools_panel or not self._child_panel:
            return False

        w, h = self.GetClientSize()
        tw = self.GetButtonWidth()
        th = self.GetButtonWidth()
        sizer = self._tools_panel.GetSizer()

        if self.IsExpanded():
            th *= sizer.GetItemCount()
            th = max(h, th)
            # fix pos and size of the child window
            x = tw
            y = 0
            pw = w - x
            ph = th - y

            self._child_panel.SetSize(wx.Size(pw, ph))
            self._child_panel.SetPosition((x, y))
            self._child_panel.Show(True)
            self._child_panel.Layout()
            if self._collapsed_tools_panel is not None:
                self._collapsed_tools_panel.Show(False)
        else:
            # fix pos and size of the child window
            x = tw
            y = 0
            pw = w - x

            self._child_panel.Show(False)
            if self._collapsed_tools_panel is not None:
                self._collapsed_tools_panel.SetSize(wx.Size(pw, th))
                self._collapsed_tools_panel.SetPosition((x, y))
                self._collapsed_tools_panel.Show(True)

        # fix pos and size of the left panel with tools
        self._tools_panel.SetPosition((0, 0))
        self._tools_panel.SetSize(wx.Size(tw, th))
        self._tools_panel.SetMinSize(wx.Size(tw, th))

        return True

    # -----------------------------------------------------------------------

    def _create_toolbar(self):
        """Create a panel with only the collapsible button."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        self._btn = self._create_collapsible_button()
        sizer.Add(self._btn, 0, wx.FIXED_MINSIZE, 0)
        self._tools_panel.SetSizer(sizer)
        w = self.GetButtonWidth()
        self._tools_panel.SetMinSize(wx.Size(w, w*2))

    # -----------------------------------------------------------------------

    def _create_collapsible_button(self):
        img_name = self._img_expanded
        if self.IsCollapsed():
            img_name = self._img_collapsed
        btn = BitmapButton(self._tools_panel, name=img_name)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_w = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_w, btn_w))
        btn.SetMinSize(wx.Size(btn_w, btn_w))
        return btn

    # -----------------------------------------------------------------------

    def _create_tool_button(self, icon, label=None):
        btn = BitmapButton(self._collapsed_tools_panel, name=icon)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_w = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_w, btn_w))
        btn.SetMinSize(wx.Size(btn_w, btn_w))
        return btn

    # -----------------------------------------------------------------------

    def _create_tool_togglebutton(self, icon, label=None):
        btn = ToggleButton(self._collapsed_tools_panel, name=icon)
        btn.SetAlign(wx.ALIGN_CENTER)
        btn.SetFocusWidth(0)
        btn.SetSpacing(0)
        btn.SetBorderWidth(0)
        btn_h = self.GetButtonWidth()
        btn.SetSize(wx.Size(btn_h, btn_h))
        btn.SetMinSize(wx.Size(btn_h, btn_h))
        return btn

    # ------------------------------------------------------------------------

    def _process_label_event(self, event):
        """Handle the wx.EVT_BUTTON event.

        :param event: a CommandEvent event to be processed.

        """
        evt_obj = event.GetEventObject()
        if evt_obj.GetName() == "slashdot":
            # Open a "window" to show the label
            win = PopupLabel(self.GetTopLevelParent(), wx.SIMPLE_BORDER, self._label)
            # Show the popup right below or above the button
            # depending on available screen space...
            pos = evt_obj.ClientToScreen((0, 0))
            # the label popup will hide the button.
            win.Position(pos, (0, 0))
            win.Show(True)

        else:
            # we shouldn't be here
            event.Skip()

# ----------------------------------------------------------------------------


class sppasFileViewPanel(sppasTimelineCollapsiblePanel):
    """Rise Panel to view&edit the content of a file in a time-view style.

    Events emitted by this class:

        - EVT_TIMELINE_VIEW

    """

    def __init__(self, parent, filename, name="baseview_risepanel"):
        super(sppasFileViewPanel, self).__init__(
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            label=filename,
            style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.BORDER_NONE,
            name=name)

        self._ft = TimelineType().unknown
        self._dirty = False
        self._filename = filename

        # Default background color ranges
        self._rgb1 = (150, 150, 150)
        self._rgb2 = (220, 220, 220)

        # Create the GUI
        self._create_content()

        # Look&feel
        try:
            settings = wx.GetApp().settings
            self.SetFont(settings.text_font)
        except AttributeError:
            self.InheritAttributes()
        self.Layout()

    # -----------------------------------------------------------------------

    def SetRandomColours(self):
        """Set background and foreground colors from our range of rgb colors."""
        # Fix the color of the background
        r, g, b = self.PickRandomBackgroundColour()
        color = wx.Colour(r, g, b)

        if (r + g + b) > 384:
            hi_color = color.ChangeLightness(90)
        else:
            hi_color = color.ChangeLightness(110)

        # Set the colors to the panel itself and to its children
        wx.Panel.SetBackgroundColour(self, color)
        self._child_panel.SetBackgroundColour(color)
        self._tools_panel.SetBackgroundColour(hi_color)
        self._collapsed_tools_panel.SetBackgroundColour(hi_color)

        min_i = min(self._rgb1 + self._rgb2 + (196,))
        fg = wx.Colour(r - min_i, g - min_i, b - min_i)
        self._child_panel.SetForegroundColour(fg)
        self._tools_panel.SetForegroundColour(fg)
        self._collapsed_tools_panel.SetForegroundColour(fg)

    # ------------------------------------------------------------------------

    def PickRandomBackgroundColour(self):
        """Return a tuple of (r,g,b) values."""
        r = random.randint(min(self._rgb1[0], self._rgb2[0]), max(self._rgb1[0], self._rgb2[0]))
        g = random.randint(min(self._rgb1[1], self._rgb2[1]), max(self._rgb1[1], self._rgb2[1]))
        b = random.randint(min(self._rgb1[2], self._rgb2[2]), max(self._rgb1[2], self._rgb2[2]))

        return r, g, b

    # ------------------------------------------------------------------------
    # About the file
    # ------------------------------------------------------------------------

    def is_unknown(self):
        return self._ft == TimelineType().unknown

    def is_audio(self):
        return self._ft == TimelineType().audio

    def is_video(self):
        return self._ft == TimelineType().video

    def is_trs(self):
        return self._ft == TimelineType().trs

    def is_image(self):
        return self._ft == TimelineType().image

    # ------------------------------------------------------------------------

    def get_filename(self):
        """Return the filename this panel is displaying."""
        return self._filename

    # ------------------------------------------------------------------------

    def set_filename(self, name):
        """Set a new name to the file.

        :param name: (str) Name of a file. It is not verified.

        """
        self._filename = name
        self.SetLabel(name)
        self._dirty = True

    # ------------------------------------------------------------------------

    def is_modified(self):
        """Return True if the content of the file has changed."""
        return self._dirty

    # -----------------------------------------------------------------------
    # Visible part
    # -----------------------------------------------------------------------

    def set_visible_period(self, start, end):
        """Fix the period of time to display (seconds).

        :param start: (int)
        :param end: (int) Time in seconds

        """
        try:
            self.GetPane().set_visible_period(start, end)
        except AttributeError:
            pass

    # -----------------------------------------------------------------------

    def set_selection_period(self, start, end):
        """Fix a period of time to highlight (seconds).

        :param start: (int)
        :param end: (int) Time in seconds

        """
        try:
            self.GetPane().set_selection_period(start, end)
        except AttributeError:
            pass

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Create the content of the panel."""
        raise NotImplementedError

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def notify(self, action, value=None):
        """Notify the parent of a TimelineViewEvent.

        The parent can catch the event with EVT_TIMELINE_VIEW.

        """
        wx.LogDebug(
            "{:s} notifies its parent {:s} of action {:s}."
            "".format(self.GetName(), self.GetParent().GetName(), action))
        evt = TimelineViewEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def update_ui(self):
        """Adapt our size to the new child size and the parent updates its layout."""
        self.Freeze()
        self.InvalidateBestSize()
        self.Thaw()
        best_size = self.GetBestSize()
        self.SetStateChange(best_size)

# ---------------------------------------------------------------------------


class TestPanel(sppasFileViewPanel):

    FILENAME = os.path.join(paths.samples, "samples-fra", "F_F_B003-P8.wav")

    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent, TestPanel.FILENAME, name="BaseView RisePanel")
        self.Collapse(False)

    def _create_content(self):
        panel = sppasPanel(self)
        st = wx.StaticText(panel, -1, self.get_filename(), pos=(10, 100))
        sz = st.GetBestSize()
        panel.SetSize((sz.width + 20, sz.height + 20))
        self.SetPane(panel)

