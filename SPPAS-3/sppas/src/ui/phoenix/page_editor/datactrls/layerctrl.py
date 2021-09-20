# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.datactrls.layerctrl.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Self-drawn control window to represent a tier in a timeline

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
import logging
import wx
import wx.lib.newevent

from sppas.src.config import paths
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata.aio.aioutils import serialize_labels
from sppas.src.anndata import sppasPoint, sppasInterval
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasAnnotation
from sppas.src.ui.phoenix.windows import sppasWindow, WindowState
from sppas.src.ui.phoenix.windows import sppasDCWindow
from sppas.src.ui.phoenix.windows.cursors import sppasCursor

from .pointctrl import sppasPointWindow
from .pointctrl import sppasEVT_POINT_MOVED
from .pointctrl import sppasEVT_POINT_RESIZED

# ---------------------------------------------------------------------------


cursor_expand_left = [
"32 32 59 1",
" 	c None",
".	c None",
"+	c #F2F2F2",
"@	c #616161",
"#	c #EAEAEA",
"$	c #E5E5E5",
"%	c #2A2A2A",
"&	c #242424",
"*	c #292929",
"=	c #E6E6E6",
"-	c #D6D6D6",
";	c #262626",
">	c #252525",
",	c #2C2C2C",
"'	c #E4E4E4",
")	c #D7D7D7",
"!	c #222222",
"~	c #E1E1E1",
"{	c #E3E3E3",
"]	c #373737",
"^	c #E2E2E2",
"/	c #272727",
"(	c #C1C1C1",
"_	c #D0D0D0",
":	c #202020",
"<	c #BDBDBD",
"[	c #C5C5C5",
"}	c #1C1C1C",
"|	c #B3B3B3",
"1	c #CCCCCC",
"2	c #232323",
"3	c #1F1F1F",
"4	c #B6B6B6",
"5	c #B9B9B9",
"6	c #1D1D1D",
"7	c #C9C9C9",
"8	c #B5B5B5",
"9	c #1B1B1B",
"0	c #C3C3C3",
"a	c #959595",
"b	c #DFDFDF",
"c	c #A0A0A0",
"d	c #282828",
"e	c #DCDCDC",
"f	c #A5A5A5",
"g	c #1E1E1E",
"h	c #DBDBDB",
"i	c #A2A2A2",
"j	c #D8D8D8",
"k	c #191919",
"l	c #AAAAAA",
"m	c #D3D3D3",
"n	c #212121",
"o	c #B0B0B0",
"p	c #333333",
"q	c #D4D4D4",
"r	c #C0C0C0",
"s	c #DADADA",
"t	c #C8C8C8",
"................................",
"................................",
"......................+@#.......",
".....................$%&*=......",
"....................-;>>>,'.....",
"...................)>>>>>>!~....",
"..................{;>>>>>>>]....",
".................^/>>>>>>>>(....",
"................_>>>>>>>>:<.....",
"...............[&>>>>>>>}|......",
"..............12>>>>>>>34.......",
".............)&>>>>>>>>[........",
"............1&>>>>>>>&_.........",
"...........52>>>>>>>67..........",
"..........82>>>>>>>90...........",
".........^!>>>>>>>/1............",
".........12>>>>>>>2{............",
"..........a3>>>>>>>:b...........",
"...........c9>>>>>>>de..........",
"............fg>>>>>>>/h.........",
".............i2>>>>>>>6j........",
"..............c2>>>>>>>k-.......",
"...............l6>>>>>>>:m......",
"................8}>>>>>>>;_.....",
".................4n>>>>>>>n_....",
"..................o&>>>>>>>p....",
"...................|!>>>>>/q....",
"....................r6>>>2s.....",
".....................tg>6_......",
"......................+@#.......",
"................................",
"................................"
]

cursor_expand_right = [
"32 32 58 1",
" 	c None",
".	c None",
"+	c #EAEAEA",
"@	c #616161",
"#	c #F2F2F2",
"$	c #E6E6E6",
"%	c #292929",
"&	c #242424",
"*	c #2A2A2A",
"=	c #E5E5E5",
"-	c #E4E4E4",
";	c #2C2C2C",
">	c #252525",
",	c #262626",
"'	c #D6D6D6",
")	c #E1E1E1",
"!	c #222222",
"~	c #D7D7D7",
"{	c #373737",
"]	c #E3E3E3",
"^	c #C1C1C1",
"/	c #272727",
"(	c #E2E2E2",
"_	c #BDBDBD",
":	c #202020",
"<	c #D0D0D0",
"[	c #B3B3B3",
"}	c #1C1C1C",
"|	c #C5C5C5",
"1	c #B6B6B6",
"2	c #1F1F1F",
"3	c #232323",
"4	c #CCCCCC",
"5	c #C9C9C9",
"6	c #1D1D1D",
"7	c #B9B9B9",
"8	c #C3C3C3",
"9	c #1B1B1B",
"0	c #B5B5B5",
"a	c #DFDFDF",
"b	c #959595",
"c	c #DCDCDC",
"d	c #282828",
"e	c #A0A0A0",
"f	c #DBDBDB",
"g	c #1E1E1E",
"h	c #A5A5A5",
"i	c #D8D8D8",
"j	c #A2A2A2",
"k	c #191919",
"l	c #D3D3D3",
"m	c #AAAAAA",
"n	c #212121",
"o	c #333333",
"p	c #B0B0B0",
"q	c #D4D4D4",
"r	c #DADADA",
"s	c #C0C0C0",
"................................",
"................................",
".......+@#......................",
"......$%&*=.....................",
".....-;>>>,'....................",
"....)!>>>>>>~...................",
"....{>>>>>>>,]..................",
"....^>>>>>>>>/(.................",
"....._:>>>>>>>><................",
"......[}>>>>>>>&|...............",
".......12>>>>>>>34..............",
"........|>>>>>>>>&~.............",
".........<&>>>>>>>&4............",
"..........56>>>>>>>37...........",
"...........89>>>>>>>30..........",
"............4/>>>>>>>!(.........",
"............]3>>>>>>>34.........",
"...........a:>>>>>>>2b..........",
"..........cd>>>>>>>9e...........",
".........f/>>>>>>>gh............",
"........i6>>>>>>>3j.............",
".......'k>>>>>>>3e..............",
"......l:>>>>>>>6m...............",
".....<,>>>>>>>}0................",
"....<n>>>>>>>n1.................",
"....o>>>>>>>&p..................",
"....q/>>>>>![...................",
".....r3>>>6s....................",
"......$%&*=.....................",
".......+@#......................",
"................................",
"................................"
]

# ---------------------------------------------------------------------------


TierEvent, EVT_TIER = wx.lib.newevent.NewEvent()
TierCommandEvent, EVT_TIER_COMMAND = wx.lib.newevent.NewCommandEvent()

# ---------------------------------------------------------------------------


class sppasTierWindow(sppasWindow):
    """A window with a DC to draw a sppasTier().

    Event emitted by this class is sppasWindowSelectedEvent() which can be
    captured with EVT_COMMAND_LEFT_CLICK.
    It is send when the tier or one of its annotation is clicked.

    Annotations of a given period are self-drawn. The selected annotation
    is stored with its index in the tier, i.e. no specific wx object to
    represent it. However, if a boundary is clicked, the wx window of a
    pointctrl is shown.

    """

    TIER_HEIGHT = 20
    SELECTION_COLOUR = wx.Colour(230, 30, 20)
    ALT_SELECTION_COLOUR = wx.Colour(30, 230, 20)
    POINT_COLOUR = wx.Colour(20, 30, 230)       # un-selected points are blue

    SELECTION_BG_COLOUR = wx.Colour(250, 170, 180)
    SELECTION_FG_COLOUR = wx.Colour(50, 70, 80)

    # -----------------------------------------------------------------------

    def __init__(self, parent, id=-1,
                 tier=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 name="tierctrl"):
        """Initialize a new sppasTierWindow instance.

        :param parent: Parent window. Must not be None.
        :param id:     A value of -1 indicates a default value.
        :param tier:   The sppasTier() to draw.
        :param pos:    If the position (-1, -1) is specified
                       then a default position is chosen.
        :param size:   If the default size (-1, -1) is specified
                       then a default size is chosen.
        :param name:   Window name.

        Two possible views: the name of the tier with its number of
        annotations or the annotations themselves. Change view with
        show_infos(): True for the 1st, False for the 2nd.

        """
        style = wx.BORDER_NONE | wx.WANTS_CHARS | wx.FULL_REPAINT_ON_RESIZE
        super(sppasTierWindow, self).__init__(parent, id, pos, size, style, name)

        # The data of this class is a sppasTier().
        self._tier = None
        if tier is not None:
            self.set_tier(tier)
        self.__selected = False

        # Show the information about the tier (True) or the annotations (False)
        self.__infos = True

        # Period of time to draw (in seconds)
        self.__period = (0., 0.)

        # the number of pixels to represent 1 second of time
        self._pxsec = 0.

        # Other members -- non-modifiable by the user
        self._min_width = 256
        self._min_height = 4
        self._vert_border_width = 0
        self._horiz_border_width = 1
        self._focus_width = 0
        self._focus_spacing = 0

        # The selection is either an annotation or a point or both or none of them
        # Index of the selected annotation in the sppasTier -- if any
        self.__ann_idx = -1
        # List of annotations of the selected point -- if any
        self.__point = sppasPointWindow(self, pos=(0, 0), size=(1, 20))
        self.__point.SetBackgroundColour(sppasTierWindow.SELECTION_COLOUR.ChangeLightness(150))
        self.__point.SetForegroundColour(sppasTierWindow.SELECTION_COLOUR)
        self.__point.Hide()
        self.__point_anns = list()  # list of ann idx

        # Allows to drag into the window -- to create an annotation
        self.__drag = False
        self.__x_dragging = 0         # start x position of drag

        # The window created when dragging -- to create an annotation
        self.__drag_window = sppasDCWindow(self, size=wx.Size(0, 0), pos=wx.Point(0, 0))
        self.__drag_window.SetBorderWidth(2)
        self.__drag_window.SetBorderColour(self.GetForegroundColour())
        self.__drag_window.Show(False)

        # Cursors while dragging
        try:
            height = wx.GetApp().settings.get_font_height()
        except Exception as e:
            height = 10
            logging.error(str(e))

        self._cursor_left = sppasCursor(cursor_expand_left, hotspot=8).create(height=int(1.8*height))
        self._cursor_right = sppasCursor(cursor_expand_right, hotspot=24).create(height=int(1.8*height))

        self.Bind(wx.EVT_SIZE, self._on_size)
        # Events related to the embedded point
        self.Bind(sppasEVT_POINT_MOVED, self._process_point_moved)
        self.Bind(sppasEVT_POINT_RESIZED, self._process_point_resized)

    # -----------------------------------------------------------------------
    # Getters about the tier and its annotations
    # -----------------------------------------------------------------------

    def get_tier(self):
        """Retrieve the object associated to the window.

        :return: sppasTier() instance.

        """
        return self._tier

    # -----------------------------------------------------------------------

    def get_tiername(self):
        """Retrieve the object name associated to the window.

        :return: (str)

        """
        if self._tier is None:
            return ""
        return self._tier.get_name()

    # -----------------------------------------------------------------------

    def is_selected(self):
        """Return True if this tier is selected."""
        return self.__selected

    # -----------------------------------------------------------------------

    def get_selected_ann(self):
        """Return the index of the currently selected annotation or -1."""
        return self.__ann_idx

    # -----------------------------------------------------------------------

    def get_selected_localization(self):
        """Return begin and end time value (float) of selected annotation."""
        if self.__ann_idx == -1:
            return 0., 0.
        ann = self._tier[self.__ann_idx]
        start, sr = self.get_ann_begin(ann)
        er, end = self.get_ann_end(ann)

        return start, end

    # -----------------------------------------------------------------------

    @staticmethod
    def get_times_point(point):
        """Return times with radius (m-r, m+r)."""
        value1 = point.get_midpoint()
        value2 = value1
        r = point.get_radius()
        if r is not None:
            value1 -= r
            value2 += r
        return value1, value2

    # -----------------------------------------------------------------------

    @staticmethod
    def get_ann_begin(ann):
        """Return times with radius (m-r, m+r)."""
        ann_begin = ann.get_lowest_localization()
        return sppasTierWindow.get_times_point(ann_begin)

    # -----------------------------------------------------------------------

    @staticmethod
    def get_ann_end(ann):
        """Return time rounded to superior milliseconds."""
        ann_end = ann.get_highest_localization()
        return sppasTierWindow.get_times_point(ann_end)

    # -----------------------------------------------------------------------
    # Setters about the tier and its annotations
    # -----------------------------------------------------------------------

    def set_tier(self, tier):
        """Set new tier content.

        :param tier: (sppasTier)

        """
        if tier is not self._tier:
            self._tier = tier
            self.SetToolTip(wx.ToolTip(self._tooltip()))

    # -----------------------------------------------------------------------

    def set_selected(self, value):
        """Select or deselect the tier.

        :param value: (bool)

        """
        value = bool(value)
        if self.__selected != value:
            self.__selected = value
            if value is True:
                self._set_state(WindowState().selected)
                if self.__ann_idx in self.__point_anns:
                    self.__point.Show(True)

            else:
                self.__ann_idx = -1
                self.__point.Show(False)
                self._set_state(WindowState().normal)

    # -----------------------------------------------------------------------

    def set_selected_ann(self, idx):
        """Set the selected annotation (do not re-draw).

        :param idx: (int) Index in the tier or -1.

        """
        if idx != self.__ann_idx:
            if idx < 0 or idx > len(self._tier):
                self.__ann_idx = -1
            else:
                self.set_selected(True)
                self.__ann_idx = idx

            if self.__ann_idx in self.__point_anns:
                self.__point.Show(True)

    # -----------------------------------------------------------------------

    def update_ann(self, idx):
        """Re-draw the tier."""
        self.Refresh()

    # -----------------------------------------------------------------------

    def delete_ann(self, idx):
        """Re-draw the tier."""
        if self.__ann_idx == idx:
            self.__ann_idx = -1
        self.Refresh()

    # -----------------------------------------------------------------------
    # About the timeline view
    # -----------------------------------------------------------------------

    def show_infos(self, value):
        """Show the tier information or the annotations of the period.

        Do not re-draw the window.

        :param value: (bool) True to show the information, False for the annotations.

        """
        self.__infos = bool(value)

    # -----------------------------------------------------------------------

    def get_visible_period(self):
        """Return (begin, end) time values of the period to draw."""
        return self.__period[0], self.__period[1]

    # -----------------------------------------------------------------------

    def set_visible_period(self, begin, end):
        """Set the period to draw (seconds).

        Do not re-draw the window.

        :param begin: (float) Begin time value (seconds)
        :param end: (float) End time value (seconds)
        :return: (bool) True if the period changed

        """
        begin = float(begin)
        end = float(end)
        if begin != self.__period[0] or end != self.__period[1]:
            self.__period = (begin, end)
            duration = end - begin
            if duration < 0.02:
                logging.warning("Period {:f}-{:f} is not large enough to "
                                "draw annotations.".format(begin, end))
                self._pxsec = 0.
            else:
                x, y, w, h = self.GetContentRect()
                self._pxsec = float(w) / duration
            return True
        return False

    # -----------------------------------------------------------------------
    # GUI -- disable focus reaction to not always re-draw the tier
    # -----------------------------------------------------------------------

    def OnGainFocus(self, event):
        """Handle the wx.EVT_SET_FOCUS event.

        :param event: a wx.FocusEvent event to be processed.

        """
        if self._state[1] == WindowState().normal:
            self._set_state(WindowState().focused, refresh=False)
            # self.Update()

    # -----------------------------------------------------------------------

    def OnLoseFocus(self, event):
        """Handle the wx.EVT_KILL_FOCUS event.

        :param event: a wx.FocusEvent event to be processed.

        """
        if self._state[1] == WindowState().focused:
            self._set_state(self._state[0], refresh=False)

    # -----------------------------------------------------------------------
    # GUI -- manage the mouse and state
    # -----------------------------------------------------------------------

    def _set_state(self, state, refresh=True):
        """Manually set the state of the window.

        :param state: (int) one of the state values

        """
        self._state[0] = self._state[1]
        self._state[1] = state

        if state == WindowState().focused:
            self._has_focus = True
        else:
            self._has_focus = False

        if self:
            if refresh is True:
                if wx.Platform == '__WXMSW__':
                    self.GetParent().RefreshRect(self.GetRect(), False)
                else:
                    self.Refresh()

    # -----------------------------------------------------------------------

    def OnMouseEnter(self, event):
        """Handle the wx.EVT_ENTER_WINDOW event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self._state[1] == WindowState().normal:
            self._set_state(WindowState().focused, refresh=False)

    # -----------------------------------------------------------------------

    def OnMouseLeftDown(self, event):
        """Handle the wx.EVT_LEFT_DOWN event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if self.IsEnabled() is True:
            self.__selected = True  # not self.__selected
            sppasWindow.OnMouseLeftDown(self, event)

    # -----------------------------------------------------------------------

    def OnMouseDragging(self, event):
        """Respond to mouse dragging event."""
        if self._state[1] == WindowState().selected and self.__infos is False:
            w, h = self.GetSize()
            x, y = self.GetPosition()     # absolute
            ex, ey = event.GetPosition()  # relative
            ex = max(0, ex)      # outside at left
            ex = min(ex, x + w)  # outside at right

            if self.__drag is False:
                # first dragging event
                self.__drag = True
                # relative position of the mouse in the window
                self.__x_dragging = ex

            ew = self.__x_dragging - ex
            if ew > 0:
                self.SetCursor(self._cursor_left)
                ew = self.__x_dragging - ex

            elif ew < 0:
                self.SetCursor(self._cursor_right)
                ew = ex - self.__x_dragging
                ex = self.__x_dragging

            # show the dragging window
            h = h - (2 * self._horiz_border_width)
            self.__drag_window.SetSize(wx.Size(ew, h))
            self.__drag_window.SetPosition(wx.Point(ex, self._horiz_border_width))
            self.__drag_window.Show(True)

    # -----------------------------------------------------------------------

    def OnMouseLeftUp(self, event):
        """Handle the wx.EVT_LEFT_UP event.

        :param event: a wx.MouseEvent event to be processed.

        """
        if not self.IsEnabled():
            return

        # Mouse was down outside of the window (but is up inside)
        if not self.HasCapture():
            return

        # Directs all mouse input to this window
        self.ReleaseMouse()

        # If the button was down when the mouse was released...
        if self._state[1] == WindowState().selected:
            if self.__selected:
                if self.__drag is True:
                    # some dragging was performed before left up.
                    self.__end_drag(success=True)
                else:
                    # the left up aims to select an annotation or a boundary
                    self._update_select_annotation(event)
                    if self._tier is not None:
                        self.notify(action="tier_selected", value=self._tier.get_name())
                    else:
                        self.NotifySelected(True)
                self._set_state(WindowState().selected)
            else:
                self._set_state(WindowState().focused)

            # test self, in case the button was destroyed in the event handler
            if self:
                event.Skip()

    # -----------------------------------------------------------------------

    def OnMouseLeave(self, event):
        """Handle the wx.EVT_LEAVE_WINDOW event.

        :param event: a wx.MouseEvent event to be processed.

        """
        # A dragging was initiated.
        if self.__drag is True:
            _, h = self.GetSize()
            _, ey = event.GetPosition()  # relative position
            if ey < 0 or ey >= h:
                # the mouse is above or below the window (i.e. not at left or right)
                self.__end_drag(success=False)

        if self.__selected is True:
            self._set_state(WindowState().selected, refresh=False)
            return

        if self._state[1] == WindowState().focused:
            self._set_state(WindowState().normal, refresh=False)
            event.Skip()

        elif self._state[1] == WindowState().selected:
            self._state[0] = WindowState().normal
            event.Skip()

        self.__selected = False

    # -----------------------------------------------------------------------

    def __end_drag(self, success):
        if success is True:
            # Create an annotation corresponding to the dragged windows
            xw, _ = self.__drag_window.GetPosition()
            ww, _ = self.__drag_window.GetSize()
            if ww > 5:
                start_midpoint = self.__period[0] + self._eval_sec(xw)
                end_midpoint = self.__period[0] + self._eval_sec(xw + ww)
                try:
                    loc = sppasInterval(sppasPoint(start_midpoint, 0.005),
                                        sppasPoint(end_midpoint, 0.005))
                    ann = sppasAnnotation(sppasLocation(loc))
                    ann_idx = self._tier.add(ann)
                    self.notify(action="ann_create", value=ann_idx)
                except Exception as e:
                    wx.LogError(str(e))

        self.__drag = False
        self.__x_dragging = 0
        self.__drag_window.Show(False)
        self.SetCursor(wx.NullCursor)

    # -----------------------------------------------------------------------
    # GUI -- draw the tier
    # -----------------------------------------------------------------------

    def DrawWindow(self):
        """Draw the Window after the WX_EVT_PAINT event. """
        width, height = self.GetClientSize()
        if not width or not height:
            # Nothing to do, we still don't have dimensions!
            return

        if self.is_selected():
            self._border_color = self.SELECTION_BG_COLOUR
        else:
            self._border_color = self.GetHighlightedColour(self.GetPenBackgroundColour(), 20)

        self.Draw()

    # -----------------------------------------------------------------------

    def DrawBackground(self, dc, gc):
        """Background is gradient from the center to top/bottom."""
        w, h = self.GetClientSize()
        if self._tier is None:
            return

        brush = self.GetBackgroundBrush()
        if brush is not None:
            dc.SetBackground(brush)
            dc.Clear()
        dc.SetBrush(brush)
        dc.SetPen(wx.TRANSPARENT_PEN)

        # Fill in the content: a gradient with a lighter color at top and bottom
        c1 = self.GetPenBackgroundColour()
        c2 = c1.ChangeLightness(175)
        mid1 = int(float(h) / 2.)
        # top-mid1 gradient
        box_rect = wx.Rect(0, 0, w, mid1)
        dc.GradientFillLinear(box_rect, c1, c2, wx.NORTH)
        # middle
        dc.DrawRectangle(0, mid1, w, mid1)
        # bottom-mid1 gradient
        box_rect = wx.Rect(0, h - mid1, w, mid1)
        dc.GradientFillLinear(box_rect, c2, c1, wx.NORTH)

    # -----------------------------------------------------------------------

    def DrawContent(self, dc, gc):
        """The content of a tier is either information or annotations."""
        if self.__infos is False:
            self.__DrawPeriodAnnotations(dc, gc)
        else:
            self.__DrawInfos(dc, gc)

    # -----------------------------------------------------------------------

    def __DrawInfos(self, dc, gc):
        """Display the information about the tier."""
        self.__point.Show(False)
        x, y, w, h = self.GetContentRect()

        # Draw the name of the tier
        tier_name = self._tier.get_name()
        tw, th = self.get_text_extend(dc, gc, tier_name)
        self.draw_label(dc, gc, tier_name, x + th, y + ((h - th) // 2))

        # Draw the number of annotations
        self.draw_label(dc, gc, str(len(self._tier)) + " annotations", x + 200, y + ((h - th) // 2))

        # Draw the index of the selected annotation
        if self.__ann_idx > -1:
            self.draw_label(dc, gc, "(-- {:d} -- is selected)".format(self.__ann_idx + 1),
                            x + 400, y + ((h - th) // 2))

    # -----------------------------------------------------------------------

    def __DrawPeriodAnnotations(self, dc, gc):
        """Draw the annotations of the current period."""
        if self._pxsec == 0.:
            self.__DrawInfos(dc, gc)

        elif self._tier.is_interval() is False:
            wx.LogWarning("Only interval tiers are supported to draw annotations.")
            self.__DrawInfos(dc, gc)

        else:
            # Display the annotations of the given period
            anns = self._tier.find(self.__period[0], self.__period[1], overlaps=True, indexes=True)

            # Draw all annotations during the period
            for ann_idx in anns:
                self._DrawAnnotation(dc, gc, ann_idx)

            # The point
            if self.__point.IsShown() and self.__point.is_dragging() is False:
                x, y, w, h = self.GetContentRect()
                xp, wp = self.xw_point(self.__point.get_point())
                self.__point.SetSize(wx.Size(wp, h))
                # hum... to get the exact position in screen, I've to shift
                # of 1 px... probably a bug of wx.
                shift = 0
                if wx.Platform == "__WXMAC__":
                    shift = -1
                self.__point.SetPosition(wx.Point(xp+shift, y))

    # -----------------------------------------------------------------------

    def _DrawAnnotation(self, dc, gc, idx):
        """Draw an annotation.

        x          x_a     xw_a        x+w
        |----------|-------|-----------|
        p0        b_a     b_e         p1

        d = p1 - p0
        d_a = annotation duration that will be displayed
        w_a = d_a * pxsec
        delay = b_a - p0  # delay between time of x and time of begin ann
        x_a = x + (delay * pxsec)

        """
        ann = self._tier[idx]
        x, y, w, h = self.GetContentRect()

        # Evaluate x and w of the begin point, and draw it
        x_a, w_pb = self.xw_point(ann.get_lowest_localization(), x)
        if w_pb > 0:
            self._DrawAnnotationPoint(dc, x_a, y, w_pb, h)

        # Evaluate x and w of the end point, and draw it
        xw_a, w_pe = self.xw_point(ann.get_highest_localization(), x, w)
        if w_pe > 0:
            self._DrawAnnotationPoint(dc, xw_a, y, w_pe, h)

        if x_a >= xw_a:
            return

        # Labels: width available for the annotation labels
        shift = 0
        if wx.Platform == "__WXMAC__":
            shift = -1
        x_l = x_a + w_pb + shift
        w_l = xw_a - x_l
        if w_l > 1:
            # Draw a rectangle for the labels background
            if idx == self.__ann_idx:
                bg_color = self.SELECTION_BG_COLOUR
            else:
                bg_color = self.GetPenBackgroundColour()
            dc.SetBrush(wx.Brush(bg_color, wx.BRUSHSTYLE_SOLID))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(x_l, y, w_l, h)

            # Draw label tags
            label = serialize_labels(ann.get_labels(), separator=" ")
            self._DrawAnnotationLabel(dc, gc, label, x_l, y, w_l, h)

    # -----------------------------------------------------------------------

    def xw_point(self, point, x=None, w=None):
        """Return (xp, wp).

        xp = x-pos of midpoint-radius
        wp = width of the point

        """
        if x is None or w is None:
            x1, y, w1, h = self.GetContentRect()
            if x is None:
                x = x1
            if w is None:
                w = w1

        # pa = time value of midpoint-radius
        # pr = time value of midpoint+radius
        pa, pr = self.get_times_point(point)

        if pr < self.__period[0]:
            return x, 0
        if pa > self.__period[1]:
            return x + w, 0
        if pr == self.__period[0]:
            return x, 1
        if pa == self.__period[1]:
            return x + w - 1, 1

        delay = pa - self.__period[0]
        xp = x + self._eval_px(delay)
        delta_time = pr - pa
        wp = max(1, self._eval_px(delta_time))

        if self.__ann_idx != -1:
            ann_selected = self._tier[self.__ann_idx]
            pss, prs = self.get_times_point(ann_selected.get_lowest_localization())
            psa, pra = self.get_times_point(ann_selected.get_highest_localization())
            if prs < pa < psa:
                # The point is inside the period of the selected annotation
                delay = psa - self.__period[0]
                d = pra - psa
                wsp = max(1, self._eval_px(d))
                xp = x + self._eval_px(delay) + wsp
                wp = 0

        return xp, wp

    # -----------------------------------------------------------------------

    def _DrawAnnotationPoint(self, dc, x, y, w, h):
        c1 = self.GetHighlightedColour(self.GetPenBackgroundColour())
        c2 = self.POINT_COLOUR

        if w > 5:
            # Fill in the content
            mid = w // 2
            box_rect = wx.Rect(x, y, mid, h)
            dc.GradientFillLinear(box_rect, c1, c2, wx.EAST)
            box_rect = wx.Rect(x+mid, y, mid, h)
            dc.GradientFillLinear(box_rect, c1, c2, wx.WEST)

        else:
            pen = wx.Pen(c2, 1, wx.SOLID)
            pen.SetCap(wx.CAP_BUTT)
            # pen.SetJoin(wx.JOIN_INVALID)
            dc.SetPen(pen)
            for i in range(w):
                dc.DrawLine(x+i, y, x+i, h+1)

    # -----------------------------------------------------------------------

    def _DrawAnnotationLabel(self, dc, gc, label, x, y, w, h):
        tw, th = self.get_text_extend(dc, gc, label)
        y = y + ((h - th) // 2)
        if th > h:
            label = ""
        min_tw, _ = self.get_text_extend(dc, gc, "...")

        while tw > w and len(label) > 0:
            # Four characters are removed
            # and a ... is added to indicate that the label is truncated
            if len(label) > 4:
                label = label[:len(label)-4]
                label += "..."
            else:
                label = label[:len(label)-1]

            tw, th = self.get_text_extend(dc, gc, label)
            if tw == min_tw:
                break
            if tw < min_tw:
                label = ""
                break

        if len(label) > 0:
            self.draw_label(dc, gc, label, x + ((w - tw) // 2), y)

    # -----------------------------------------------------------------------

    def _tooltip(self):
        """Set a tooltip string indicating data content."""
        if self._tier is not None:
            msg = self._tier.get_name() + ": "
            msg += str(len(self._tier))+" annotations"
            return msg

        return "No data"

    # -----------------------------------------------------------------------

    def SetVertBorderWidth(self, value):
        """Set the width of the left/right borders.

        :param value: (int) Border size. Not applied if not appropriate.

        """
        return

    # ------------------------------------------------------------------------

    def _eval_px(self, duration):
        """Return the number of pixels to represent the given duration."""
        return int(float(duration) * float(self._pxsec))

    def _eval_sec(self, width):
        """Return the duration represented by the given number of pixels."""
        return float(width) / float(self._pxsec)

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def notify(self, action, value=None):
        """Send an EVT_TIER event to the listener (if any)."""
        evt = TierEvent(action=action, value=value)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------

    def _update_select_annotation(self, event):
        if self._pxsec <= 0.0001:
            return False

        # Time interval of the clicked position with a small delay around
        time_value1, time_value2 = self.__position_to_times(event.GetPosition())

        # Before doing things that takes time, we'll see if this time
        # value is a bound of the currently selected ann.
        if self.__ann_idx != -1:
            # an annotation is currently selected
            cur_ann = self._tier[self.__ann_idx]
            show_point = self.__fix_pointctrl(cur_ann, time_value1, time_value2)
            self.__point.Show(show_point)
            if show_point is True:
                # one of the bound of the currently selected ann was clicked
                self.__point_anns = [self.__ann_idx]
                # There's no need to re-draw the layer
                return False

        # Which annotation(s) was clicked
        ann_idx = self._tier.mindex(time_value1, bound=2)
        ann = self._tier[ann_idx]
        anns = list()
        while ann.get_lowest_localization() <= time_value2:
            anns.append(ann_idx)
            ann_idx += 1
            if ann_idx == len(self._tier):
                break
            ann = self._tier[ann_idx]

        if len(anns) == 0:
            # this situation occurs when a hole is clicked (background of the layer)
            # so no annotation is clicked... the selected point is disabled
            self.__point.Show(False)
            self.__point_anns = list()
            self.__point.cancel_point()
            # but the currently selected annotation is not changed
            return False

        elif len(anns) == 1:
            # an/one annotation was clicked
            ann_idx = anns[0]
            self.__point.SetForegroundColour(sppasTierWindow.SELECTION_COLOUR)
            self.__point.SetBackgroundColour(sppasTierWindow.SELECTION_COLOUR.ChangeLightness(150))

        else:
            # more than one annotation was clicked
            self.__point.SetForegroundColour(sppasTierWindow.ALT_SELECTION_COLOUR)
            self.__point.SetBackgroundColour(sppasTierWindow.ALT_SELECTION_COLOUR.ChangeLightness(150))
            # an annotation was clicked but at this time value, there
            # are several ones... HOW TO CHOOSE WHICH ONE TO SELECT ?????
            if self.__ann_idx not in anns:
                tv = (time_value1 + time_value2) / 2.
                ann_idx = self._tier.mindex(tv, bound=2)
            else:
                # or keep the current one if it is inside the found anns
                ann_idx = self.__ann_idx

        show_point = self.__fix_pointctrl(self._tier[ann_idx], time_value1, time_value2)
        self.__point.Show(show_point)
        if show_point is True:
            self.__point_anns = anns
        else:
            # the label of an annotation was clicked
            if ann_idx in self.__point_anns:
                self.__point.Show(False)
                self.__point_anns = list()
                self.__point.cancel_point()

        # The new selected annotation is different of the previous one
        if ann_idx != self.__ann_idx:
            self.__ann_idx = ann_idx
            return True

        return False

    # -----------------------------------------------------------------------

    def __position_to_times(self, pos):
        """Return a time interval of the position with a small delay around."""
        x, _ = pos
        if wx.Platform == "__WXMAC__":
            x = x + 1  # under macos, the position we get is before the cursor
        screen_width, _ = wx.GetDisplaySize()  # proportional to HD
        d = screen_width // 1920
        if self._pxsec < 400.:
            d = d * 4
        elif self._pxsec < 800:
            d = d * 3
        elif self._pxsec < 1200:
            d = d * 2
        time_value1 = self.__period[0] + self._eval_sec(x - d)
        time_value2 = self.__period[0] + self._eval_sec(x + d)
        # logging.debug("-->> Pos to Time: pxsec={}, screen_width={} => d={} ==>> {} - {}".format(self._pxsec, screen_width, d, time_value1, time_value2))

        return time_value1, time_value2

    # -----------------------------------------------------------------------

    def __fix_pointctrl(self, ann, time_value1, time_value2):
        x, y, w, h = self.GetContentRect()
        if time_value1 <= ann.get_lowest_localization() <= time_value2:
            xp, wp = self.xw_point(ann.get_lowest_localization(), x, w)
            self.__point.SetSize(wx.Size(wp, h))
            self.__point.SetPosition(wx.Point(xp, y))
            self.__point.set_point(ann.get_lowest_localization())
            return True

        if time_value1 <= ann.get_highest_localization() <= time_value2:
            xp, wp = self.xw_point(ann.get_highest_localization(), x, w)
            self.__point.SetSize(wx.Size(wp, h))
            self.__point.SetPosition(wx.Point(xp, y))
            self.__point.set_point(ann.get_highest_localization())
            return True

        return False

    # -----------------------------------------------------------------------
    # Callbacks to events
    # -----------------------------------------------------------------------

    def _on_size(self, event):
        """Our size changed. We need to re-estimate pxsec before re-draw."""
        x, y, w, h = self.GetContentRect()
        prev_pxsec = self._pxsec
        duration = self.__period[1] - self.__period[0]
        middle = duration / 2.
        if duration < 0.02:
            self._pxsec = 0.
        else:
            self._pxsec = float(w) / duration

        # logging.debug(" ... pixels / second = {:f}".format(self._pxsec))
        # Re-draw only if the new pxsec is significantly different
        delay = middle - self.__period[0]
        x_old = x + int(delay * prev_pxsec)
        x_new = x + int(delay * self._pxsec)
        if x_old != x_new:
            self.Refresh()

    # -----------------------------------------------------------------------

    def _process_point_moved(self, event):
        """The point was moved by dragging it: new midpoint value."""
        pointctrl = event.GetEventObject()
        # Evaluate the new midpoint value
        px, _ = event.pos
        pw, _ = event.size
        old_time_value = pointctrl.get_midpoint()
        time_value = self.__period[0] + self._eval_sec(px + pw//2)
        logging.debug("The pointctrl at midpoint {:f} was moved to {:f}"
                      "".format(old_time_value, time_value))

        # get all anns having this point, remove them of the tier
        copied_anns = list()
        for ann_idx in reversed(sorted(self.__point_anns)):
            ann = self._tier[ann_idx]
            ann.set_parent(None)
            copied = ann.copy()
            try:
                logging.debug(" ... will pop ann {} at index {}".format(ann, ann_idx))
                self._tier.pop(ann_idx)
                logging.debug(" ... append copied {}".format(copied))
                copied_anns.append(copied)
            except Exception as e:
                wx.LogError(str(e))
                # Invalidate the changes
                pointctrl.RestorePosition()
                for ann in copied_anns:
                    self._tier.add(ann)
                self.Refresh()
                return

        logging.debug(" ... all {:d} anns removed successfully of the tier".format(len(copied_anns)))

        # Set the new midpoint value to all copied anns
        recopied_anns = list()
        for a in copied_anns:
            recopied_anns.append(a.copy())

        ann_indexes = self.__point_anns
        added_indexes = list()
        for ann in copied_anns:
            copied = ann.copy()
            begin_point = ann.get_lowest_localization()
            end_point = ann.get_highest_localization()
            changed_point = None
            if old_time_value == begin_point:
                begin_point = sppasPoint(time_value, begin_point.get_radius())
                changed_point = begin_point
            elif old_time_value == end_point:
                end_point = sppasPoint(time_value, begin_point.get_radius())
                changed_point = end_point

            try:
                ann.set_best_localization(sppasInterval(begin_point, end_point))
                add_ann_idx = self._tier.add(ann)
                pointctrl.set_point(changed_point)
                added_indexes.append(add_ann_idx)
                if add_ann_idx not in ann_indexes:
                    ann_indexes.append(add_ann_idx)
            except Exception as e:
                wx.LogError(str(e))
                # Invalidate the changes
                for ai in added_indexes:
                    self._tier.pop(ai)
                for a in recopied_anns:
                    self._tier.add(a)
                pointctrl.RestorePosition()
                self.Refresh()
                return

        # No error.
        for ann_idx in sorted(ann_indexes):
            self.notify(action="ann_update", value=ann_idx)

        self.Refresh()

    # -----------------------------------------------------------------------

    def _process_point_resized(self, event):
        """The point was resized by dragging it: new radius value."""
        pointctrl = event.GetEventObject()
        midpoint = pointctrl.get_midpoint()
        # Evaluate the new radius value
        px, _ = event.pos
        pw, _ = event.size
        time_value = round(self._eval_sec(pw//2), 6)
        logging.debug("The point at {:f} has new radius {:f}".format(midpoint, time_value))

        # Set the new radius value to all annotations having this point
        for ann_idx in self.__point_anns:
            ann = self._tier[ann_idx]
            begin_point = ann.get_lowest_localization()
            end_point = ann.get_highest_localization()
            if midpoint == begin_point:
                begin_point.set_radius(time_value)
            if midpoint == end_point:
                end_point.set_radius(time_value)
            try:
                ann.set_best_localization(sppasInterval(begin_point, end_point))
                self.notify(action="ann_update", value=ann_idx)
                self.Refresh()
            except Exception as e:
                # Invalidate the changes
                pointctrl.RestorePosition()
                pointctrl.RestoreSize()
                wx.LogError(str(e))

# ---------------------------------------------------------------------------


class TestPanel(wx.Panel):
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
        self.p1 = sppasTierWindow(self, pos=(10, 10), size=(300, 24), tier=trs[0])
        self.p1.set_visible_period(2.49, 6.49)
        self.p1.SetBackgroundColour(wx.YELLOW)
        self.p1.show_infos(False)
        self.p1.set_selected_ann(5)
        self.p1.Refresh()

        # show annotations, not information
        self.p2 = sppasTierWindow(self, pos=(10, 100), size=(300, 48), tier=trs[1])
        self.p2.set_visible_period(2.49, 6.49)
        self.p2.SetBackgroundColour(wx.LIGHT_GREY)
        self.p2.show_infos(False)
        self.p2.Refresh()

        # show information, not annotations
        self.p3 = sppasTierWindow(self, pos=(10, 100), size=(300, 64), tier=trs[1])
        self.p3.SetBackgroundColour(wx.Colour(200, 240, 220))
        self.p3.show_infos(True)
        self.p3.Refresh()

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(btn, 0, wx.EXPAND)
        s.Add(self.p1, 0, wx.EXPAND)
        s.Add(self.p2, 0, wx.EXPAND)
        s.Add(self.p3, 0, wx.EXPAND)
        self.SetSizer(s)
        self.Bind(wx.EVT_COMMAND_LEFT_CLICK, self._process_selected)

    # -----------------------------------------------------------------------

    def _process_selected(self, event):
        tierctrl = event.GetEventObject()
        wx.LogDebug("Selected event received. Tier {} is selected. Ann: {}"
                    "".format(tierctrl.get_tiername(), tierctrl.get_selected_ann()))

    # -----------------------------------------------------------------------

    def _switch_view(self, event):
        self._show_info = not self._show_info
        self.p1.show_infos(self._show_info)
        self.p2.show_infos(self._show_info)
        self.p3.show_infos(self._show_info)
        self.p1.Refresh()
        self.p2.Refresh()
        self.p3.Refresh()
