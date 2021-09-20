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

    src.ui.phoenix.windows.datactrls.tierctrl.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import logging
import wx
from math import ceil, floor

from sppas.src.config import paths
from sppas.src.anndata import sppasTrsRW

from sppas.src.ui.phoenix.windows.panels import sppasPanel

from src.ui.phoenix.page_editor.datactrls.deprecated.basedatactrl import sppasDataWindow
from src.ui.phoenix.page_editor.datactrls.deprecated.annctrl import sppasAnnotationWindow

# ---------------------------------------------------------------------------


class sppasTierWindow(sppasDataWindow):
    """A window with a DC to draw a sppasTier().

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    Event emitted by this class is sppasWindowSelectedEvent() which can be
    captured with EVT_COMMAND_LEFT_CLICK.
    It is send when the tier or one of its annotation is clicked.

    """

    TIER_HEIGHT = 20
    SELECTION_COLOUR = wx.Colour(250, 30, 20)

    # -----------------------------------------------------------------------

    def __init__(self, parent, id=-1,
                 data=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name="tierctrl"):
        """Initialize a new sppasTierWindow instance.

        :param parent: Parent window. Must not be None.
        :param id:     A value of -1 indicates a default value.
        :param data:   Data to draw.
        :param pos:    If the position (-1, -1) is specified
                       then a default position is chosen.
        :param size:   If the default size (-1, -1) is specified
                       then a default size is chosen.
        :param name:   Window name.

        Two possible views: the name of the tier with its number of
        annotations or the annotations themselves. Change view with
        show_infos(): True for the 1st, False for the 2nd.

        """
        style = wx.BORDER_NONE | wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE
        super(sppasTierWindow, self).__init__(
            parent, id, data, pos, size, style, name)

        self._data = None
        if data is not None:
            self.SetData(data)

        self.__infos = True
        self.__ann_idx = -1
        self.__period = (0., 0.)
        self._pxsec = 0   # the number of pixels to represent 1 second of time
        self.__annctrls = dict()

        # Override parent members
        self._is_selectable = True
        self._min_width = 256
        self._min_height = 4
        self._vert_border_width = 0
        self._horiz_border_width = 1
        self._focus_width = 0
        self.SetBorderColour(self.GetBackgroundColour())

    # -----------------------------------------------------------------------
    # Switch the view
    # -----------------------------------------------------------------------

    def show_infos(self, value):
        """Show the tier information or the annotations of the period.

        Do not Refresh the tier.

        :param value: (bool) True to show the information, False for the annotations.

        """
        self.__infos = bool(value)

    # -----------------------------------------------------------------------

    def SetSelected(self, value):
        """Override. Select or deselect the window except if not selectable.

        :param value: (bool)

        """
        # Ok, do normal things to do if this ann is selected or de-selected
        sppasDataWindow.SetSelected(self, value)

        # and update its children annctrls
        if self.IsSelected() is False:
            self.SetBorderColour(self.GetBackgroundColour())
            for ann in self.__annctrls:
                if self.__annctrls[ann].IsSelected() is True:
                    self.__annctrls[ann].SetSelected(False)
                    self.__annctrls[ann].Refresh()
                self.__ann_idx = -1

        else:
            self.SetBorderColour(self.SELECTION_COLOUR)

    # -----------------------------------------------------------------------

    def Notify(self):
        """Override."""
        if self.IsSelected() is True:
            sppasDataWindow.Notify(self)
        else:
            # Do not accept a self-deselection with the click.
            self.SetSelected(True)

    # -----------------------------------------------------------------------

    def get_visible_period(self):
        """Return (begin, end) time values of the period to draw."""
        return self.__period[0], self.__period[1]

    # -----------------------------------------------------------------------

    def set_visible_period(self, begin, end):
        """Set the period to draw (seconds) and Refresh."""
        if begin != self.__period[0] or end != self.__period[1]:
            self.__period = (begin, end)
            self.Refresh()

    # -----------------------------------------------------------------------

    def get_selected_ann(self):
        """Return the index of the currently selected annotation."""
        return self.__ann_idx

    # -----------------------------------------------------------------------

    def get_selected_localization(self):
        """Return begin and end time value (float)."""
        if self.__ann_idx == -1:
            return 0., 0.
        ann = self._data[self.__ann_idx]
        start = self.get_ann_begin(ann)
        end = self.get_ann_end(ann)

        return start, end

    # -----------------------------------------------------------------------

    def set_selected_ann(self, idx):
        if idx == self.__ann_idx:
            return

        # The currently selected ann has to be de-selected.
        if self.__ann_idx != -1:
            ann_sel = self._data[self.__ann_idx]
            self.__annctrls[ann_sel].SetSelected(False)
            self.__annctrls[ann_sel].Refresh()

        # The current ann selection index must be updated
        self.__ann_idx = idx

        # The newly selected annotation must be re-drawn to be highlighted.
        if idx != -1:
            # if the newly selected annotation was never drawn, it still hasn't an annctrl
            ann = self._data[idx]
            if ann not in self.__annctrls:
                self.__create_annctrl(ann)
            self.__annctrls[ann].SetSelected(True)
            if self.IsSelected() is True:
                self.__annctrls[ann].Refresh()

            if self.IsSelected() is False:
                self.SetSelected(True)
                self.Refresh()

    # -----------------------------------------------------------------------

    def update_ann(self, idx):
        logging.debug("an annotation was modified : {}".format(idx))
        ann = self._data[idx]
        self.__annctrls[ann].Refresh()

    # -----------------------------------------------------------------------

    def delete_ann(self, idx):
        logging.debug("an annotation was deleted : {}".format(idx))
        # ??? how to destroy the corresponding annctrl ? the ann was deleted...
        self.Refresh()

    # -----------------------------------------------------------------------

    def get_tiername(self):
        return self._data.get_name()

    # -----------------------------------------------------------------------

    @staticmethod
    def get_ann_begin(ann):
        """Return time rounded to inferior milliseconds."""
        ann_begin = ann.get_lowest_localization()
        value = ann_begin.get_midpoint()
        r = ann_begin.get_radius()
        if r is not None:
            value -= r
        return float(floor(value*1000.)) / 1000.

    # -----------------------------------------------------------------------

    @staticmethod
    def get_ann_end(ann):
        """Return time rounded to superior milliseconds."""
        ann_end = ann.get_highest_localization()
        value = ann_end.get_midpoint()
        r = ann_end.get_radius()
        if r is not None:
            value += r
        return float(ceil(value*1000.)) / 1000.

    # -----------------------------------------------------------------------
    # GUI
    # -----------------------------------------------------------------------

    def DrawBackground(self, dc, gc):
        x, y, w, h = self.GetContentRect()
        brush = self.GetBackgroundBrush()
        if brush is not None:
            dc.SetBackground(brush)
            dc.Clear()
        dc.SetBrush(brush)
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, 0, w, h)

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """The content of a tier is either information or annotations."""
        if self.__infos is False:
            self.__DrawPeriodAnnotations(dc, gc)
        else:
            self.__DrawInfos(dc, gc)

    # -----------------------------------------------------------------------

    def __DrawPeriodAnnotations(self, dc, gc):
        x, y, w, h = self.GetContentRect()
        duration = float(self.__period[1]) - float(self.__period[0])
        if duration < 0.02:
            wx.LogWarning("Period is not large enough to draw annotations.")
            self.__DrawInfos(dc, gc)
        elif self._data.is_interval() is False:
            wx.LogWarning("Only interval tiers are supported to draw annotations.")
            self.__DrawInfos(dc, gc)
        else:
            # Display the annotations of the given period
            self._pxsec = int(float(w) / duration)
            anns = self._data.find(self.__period[0], self.__period[1], overlaps=True)
            # Hide annotations out of the period
            for ann in self.__annctrls:
                if ann not in anns:
                    self.__annctrls[ann].Hide()
            # Show all annotations during the period
            for ann in anns:
                self._DrawAnnotation(ann, x, y, w, h)

    # -----------------------------------------------------------------------

    def __DrawInfos(self, dc, gc):
        x, y, w, h = self.GetContentRect()

        # Do not display any of the annotations
        for ann in self.__annctrls:
            self.__annctrls[ann].Hide()

        # Draw infos instead
        tier_name = self._data.get_name()
        tw, th = self.get_text_extend(dc, gc, tier_name)
        self.draw_label(dc, gc, tier_name, x, y + ((h - th) // 2))
        self.draw_label(dc, gc, str(len(self._data)) + " annotations", x + 200, y + ((h - th) // 2))
        if self.__ann_idx > -1:
            self.draw_label(dc, gc, "(-- {:d} -- is selected)".format(self.__ann_idx + 1),
                            x + 400, y + ((h - th) // 2))

    # -----------------------------------------------------------------------

    def _DrawAnnotation(self, ann, x, y, w, h):
        """Draw an annotation.

        x          x_a                x+w
        |----------|-------|-----------|
        p0        b_a     b_e         p1

        d = p1 - p0
        d_a = annotation duration that will be displayed
        w_a = d_a * pxsec
        x_a ?
        delay = b_a - p0  # delay between time of x and time of begin ann

        """
        draw_points = [True, True]
        # estimate the displayed duration of the annotation
        b_a = self.get_ann_begin(ann)
        e_a = self.get_ann_end(ann)
        if b_a < self.__period[0]:
            b_a = self.__period[0]
            draw_points[0] = False
        if e_a > self.__period[1]:
            e_a = self.__period[1]
            draw_points[1] = False
        d_a = e_a - b_a
        # annotation width
        w_a = d_a * self._pxsec
        # annotation x-axis
        if self.__period[0] == b_a:
            x_a = x
        else:
            delay = b_a - self.__period[0]
            d = float(self.__period[1]) - float(self.__period[0])
            x_a = x + int((float(w) * delay) / d)
        pos = wx.Point(x_a, y)
        size = wx.Size(int(w_a), h)

        if ann not in self.__annctrls:
            self.__create_annctrl(ann)

        annctrl = self.__annctrls[ann]
        annctrl.SetPxSec(self._pxsec)
        annctrl.SetPosition(pos)
        annctrl.SetSize(size)
        annctrl.ShouldDrawPoints(draw_points)
        annctrl.Show()

    # -----------------------------------------------------------------------

    def _tooltip(self):
        """Set a tooltip string indicating data content."""
        if self._data is not None:
            msg = self._data.get_name() + ": "
            msg += str(len(self._data))+" annotations"
            return msg

        return "No data"

    # -----------------------------------------------------------------------

    def _process_ann_selected(self, event):
        """An annotation was clicked.

        """
        # Which annotation was clicked?
        annctrl_click = event.GetEventObject()
        ann_click = event.GetObj()
        sel_click = event.GetSelected()

        # We'll forbid an annotation to self-deselect
        if sel_click is False:
            # the annotation was selected and it self-deselected by the click.
            annctrl_click.SetSelected(True)

        else:

            idx = self._data.get_annotation_index(ann_click)
            self.set_selected_ann(idx)

            """
            # The currently selected ann has to be de-selected.
            if self.__ann_idx != -1:
                ann_sel = self._data[self.__ann_idx]
                self.__annctrls[ann_sel].SetSelected(False)
                self.__ann_idx = -1

            # The current ann selection index must be updated
            self.__ann_idx = self._data.get_annotation_index(ann_click)

            # Notify the parent this tier/an annotation of this tier was selected
            if self.IsSelected() is False:
                self.SetSelected(True)
            """
            self.Notify()

    # -----------------------------------------------------------------------

    def __create_annctrl(self, ann):
        annctrl = sppasAnnotationWindow(self, data=ann)
        annctrl.SetBackgroundColour(self.GetBackgroundColour())
        annctrl.SetForegroundColour(self.GetForegroundColour())
        annctrl.SetPxSec(self._pxsec)
        annctrl.Bind(wx.EVT_COMMAND_LEFT_CLICK, self._process_ann_selected)
        self.__annctrls[ann] = annctrl

# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):
    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent,
            style=wx.BORDER_NONE | wx.WANTS_CHARS,
            name="Test TierCtrl")

        filename = os.path.join(paths.samples, "annotation-results", "samples-fra", "F_F_B003-P8-palign.xra")
        parser = sppasTrsRW(filename)
        trs = parser.read()

        btn = wx.Button(self, size=wx.Size(120, 40), label="Show info/ann")
        btn.Bind(wx.EVT_BUTTON, self._switch_view)
        self._show_info = False

        # show annotations, not information
        self.p1 = sppasTierWindow(self, pos=(10, 10), size=(300, 24), data=trs[0])
        self.p1.set_visible_period(2.49, 3.49)
        self.p1.SetBackgroundColour(wx.YELLOW)
        self.p1.show_infos(False)

        # show annotations, not information
        self.p2 = sppasTierWindow(self, pos=(10, 100), size=(300, 48), data=trs[1])
        self.p2.set_visible_period(2.49, 3.49)
        self.p2.SetBackgroundColour(wx.LIGHT_GREY)
        self.p2.show_infos(False)

        # show information, not annotations
        self.p3 = sppasTierWindow(self, pos=(10, 100), size=(300, 64), data=trs[1])
        self.p3.SetBackgroundColour(wx.Colour(200, 240, 220))
        self.p2.show_infos(False)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(btn, 0, wx.EXPAND)
        s.Add(self.p1, 0, wx.EXPAND)
        s.Add(self.p2, 0, wx.EXPAND)
        s.Add(self.p3, 0, wx.EXPAND)
        self.SetSizer(s)
        self.Bind(wx.EVT_COMMAND_LEFT_CLICK, self._process_selected)

    # -----------------------------------------------------------------------

    def _process_selected(self, event):
        tier = event.GetObj()
        value = event.GetSelected()
        wx.LogDebug("Selected event received. Tier {} is selected {}"
                    "".format(tier.get_name(), value))

    # -----------------------------------------------------------------------

    def _switch_view(self, event):
        self._show_info = not self._show_info
        self.p1.show_infos(self._show_info)
        self.p2.show_infos(self._show_info)
        self.p3.show_infos(self._show_info)
        self.p1.Refresh()
        self.p2.Refresh()
        self.p3.Refresh()
