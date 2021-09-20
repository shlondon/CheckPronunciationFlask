# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_editor.media.smmpctrl.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A base class panel to display buttons for a media player.

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

The main class to control a multi media player.

Requires the following libraries:

 - simpleaudio, installed by the audioplay feature;
 - opencv, installed by the videoplay feature.

"""

import wx
import os
import wx.lib.gizmos as gizmos

from sppas.src.config import paths  # used only in the Test Panel

from sppas.src.ui.phoenix.windows.buttons import BitmapButton
from sppas.src.ui.phoenix.windows.buttons import BitmapTextButton
from sppas.src.ui.phoenix.windows.buttons import ToggleButton
from sppas.src.ui.phoenix.windows.panels import sppasPanel
from sppas.src.ui.phoenix.windows.frame import sppasImageFrame

from .mediaevents import MediaEvents
from .smmps import sppasMMPS
from .playerctrlspanel import sppasPlayerControlsPanel

# ---------------------------------------------------------------------------


class sppasMMPCtrl(sppasPlayerControlsPanel):
    """Create a panel with controls to manage media.

    This class is inheriting a PlayerControl and embedding a SMMPS because
    it failed to instantiate when it was inheriting both.

    """

    def __init__(self, parent,
                 id=wx.ID_ANY,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=0,
                 name="smmpc_panel"):
        """Create a sppasPlayerControlsPanel embedding a sppasMMPS.

        :param parent: (wx.Window) Parent window must NOT be none
        :param id: (int) window identifier or -1
        :param pos: (wx.Pos) the control position
        :param size: (wx.Size) the control size
        :param style: (int) the underlying window style
        :param name: (str) the widget name.

        """
        super().__init__(parent, id, pos, size, style, name)

        self.__smmps = sppasMMPS(owner=self)
        self._create_mmpc_content()
        self._setup_mmpc_events()

        try:
            s = wx.GetApp().settings
            self.SetBackgroundColour(s.bg_color)
            self.SetForegroundColour(s.fg_color)
            self.SetFont(s.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, colour):
        """Set the background of our panel to the given color or hi-color."""
        wx.Panel.SetBackgroundColour(self, colour)
        hi_color = self.GetHighlightedBackgroundColour()

        for name in ("transport", "widgets_left", "widgets_right", "slider"):
            w = self.FindWindow(name + "_panel")
            w.SetBackgroundColour(colour)
            for c in w.GetChildren():
                if isinstance(c, ToggleButton) is True:
                    c.SetBackgroundColour(hi_color)
                else:
                    c.SetBackgroundColour(colour)

        self.led.SetBackgroundColour(colour)

    # -----------------------------------------------------------------------

    def SetForegroundColour(self, colour):
        """Set the foreground of our panel to the given color."""
        wx.Panel.SetForegroundColour(self, colour)
        self._set_led_fg_color()

        for name in ("transport", "widgets_left", "widgets_right", "slider"):
            w = self.FindWindow(name + "_panel")
            w.SetForegroundColour(colour)
            for c in w.GetChildren():
                if c != self.led:
                    c.SetForegroundColour(colour)

    # ----------------------------------------------------------------------

    def _set_led_fg_color(self):
        # The led has its own color, whatever the given one.
        period = self._timeslider.get_range()
        if period[0] == period[1]:
            # self.led.SetForegroundColour(self.GetBackgroundColour())
            self.led.SetForegroundColour(self.GetForegroundColour())
        else:
            if self._timeslider.is_selection() is True:
                # pinky-red
                self.led.SetForegroundColour(self._timeslider.SELECTION_FG_COLOUR)
            else:
                # blue like the toggled button
                self.led.SetForegroundColour(wx.Colour(30, 80, 210))

    # -----------------------------------------------------------------------

    def GetHighlightedBackgroundColour(self):
        """Return a color slightly different of the parent background one."""
        color = self.GetBackgroundColour()
        r, g, b, a = color.Red(), color.Green(), color.Blue(), color.Alpha()
        return wx.Colour(r, g, b, a).ChangeLightness(95)

    # -----------------------------------------------------------------------
    # Manage the timeslider
    # -----------------------------------------------------------------------

    def show_range(self, value=True):
        """Show the indicator of the currently selected range of time. """
        self._timeslider.show_range(value)
        self.SetMinSize(self.DoGetBestSize())

    def show_rule(self, value=True):
        """Show the ruler of the current visible range of time. """
        self._timeslider.show_rule(value)
        self.SetMinSize(self.DoGetBestSize())

    def get_visible_range(self):
        """Return the visible time range."""
        return self._timeslider.get_visible_range()

    def set_visible_range(self, start, end):
        """Set the visible time range."""
        self._timeslider.set_visible_range(start, end)

    def get_selection_range(self):
        """Return the selection time range."""
        return self._timeslider.get_selection_range()

    def set_selection_range(self, start, end):
        """Set the selection time range."""
        self._timeslider.set_selection_range(start, end)

    def is_tiers_annotations(self):
        """Return true if the button to show tier annotations is toggled."""
        return self.FindWindow("tier_infos").GetValue()

    def is_audios_waveform(self):
        """Return true if the button to show audio waveform is toggled."""
        return self.FindWindow("sound_wave_lines").GetValue()

    # -----------------------------------------------------------------------
    # Construct the panel
    # -----------------------------------------------------------------------

    def _create_mmpc_content(self):
        """Add widgets to the content of this panel."""

        led = gizmos.LEDNumberCtrl(self._transport_panel, style=wx.BORDER_NONE, name="moment_led")
        led.SetValue("0.000")
        led.SetAlignment(gizmos.LED_ALIGN_RIGHT)
        led.SetDrawFaded(False)
        led.SetMinSize(wx.Size(self.get_font_height()*10, self._btn_size))
        self._transport_panel.GetSizer().Prepend(led, 0, wx.ALIGN_CENTER | wx.ALL, sppasPanel.fix_size(2))
        # The led has it's own colors that we have to override
        self._set_led_fg_color()
        self.led.SetBackgroundColour(self.GetBackgroundColour())

        # -------

        btn1 = BitmapButton(self.widgets_left_panel, name="scroll_left")
        self.SetButtonProperties(btn1)
        self.AddLeftWidget(btn1)
        btn1.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn3 = BitmapButton(self.widgets_left_panel, name="expand_false")
        self.SetButtonProperties(btn3)
        self.AddLeftWidget(btn3)
        btn3.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn4 = BitmapButton(self.widgets_left_panel, name="expand_true")
        self.SetButtonProperties(btn4)
        self.AddLeftWidget(btn4)
        btn4.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn7 = BitmapButton(self.widgets_left_panel, name="scroll_zoom_all")
        self.SetButtonProperties(btn7)
        self.AddLeftWidget(btn7)
        btn7.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn5 = BitmapButton(self.widgets_left_panel, name="scroll_to_selection")
        self.SetButtonProperties(btn5)
        self.AddLeftWidget(btn5)
        btn5.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn6 = BitmapButton(self.widgets_left_panel, name="scroll_zoom_selection")
        self.SetButtonProperties(btn6)
        self.AddLeftWidget(btn6)
        btn6.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btn2 = BitmapButton(self.widgets_left_panel, name="scroll_right")
        self.SetButtonProperties(btn2)
        self.AddLeftWidget(btn2)
        btn2.Bind(wx.EVT_BUTTON, self._on_set_visible)

        # -------

        btn_sort = BitmapButton(self.widgets_right_panel, name="sort")
        btn_sort.SetToolTip("Sort opened files")
        self.SetButtonProperties(btn_sort)
        self.AddRightWidget(btn_sort)
        btn_sort.Bind(wx.EVT_BUTTON, self._on_set_visible)

        btnr1 = ToggleButton(self.widgets_right_panel, name="tier_infos")
        btnr1.SetToolTip("Either show annotations of tiers or information")
        self.SetButtonProperties(btnr1)
        self.AddRightWidget(btnr1)
        btnr1.Bind(wx.EVT_TOGGLEBUTTON, self._on_set_visible)

        btnr2 = ToggleButton(self.widgets_right_panel, name="sound_wave_lines")
        btnr2.SetToolTip("Incoming in next version: Show waveform of audio files")
        self.SetButtonProperties(btnr2)
        self.AddRightWidget(btnr2)
        btnr2.Bind(wx.EVT_TOGGLEBUTTON, self._on_set_visible)

    # -----------------------------------------------------------------------

    @property
    def led(self):
        return self.FindWindow("moment_led")

    # -----------------------------------------------------------------------
    # Overridden methods...
    # -----------------------------------------------------------------------

    def play(self):
        """Start playing all the enabled media."""
        played = False
        if self.__smmps.is_playing() is False and self.__smmps.is_loading() is False:
            if self.__smmps.is_paused() is False:
                # get the period to play
                start, end = self._timeslider.get_range()
                try:
                    self.__smmps.set_period(start, end)
                except ValueError as e:
                    wx.LogError(str(e))
                    return False

            played = self.__smmps.play()
            if played is True:
                # self.prev_time = datetime.datetime.now()
                self.FindWindow("media_pause").SetValue(False)

        return played

    # -----------------------------------------------------------------------

    def pause(self):
        """Pause in playing the media."""
        pause_status = self.FindWindow("media_pause").GetValue()

        # It was asked to pause
        if pause_status is True:
            # and the audio is not already paused
            if self.__smmps.is_paused() is False:
                paused = self.__smmps.pause()
                if paused is not True:
                    # but paused was not done in the audio
                    self.FindWindow("media_pause").SetValue(False)
                else:

                    # Put the slider exactly at the right time position
                    position = self.__smmps.tell()
                    self._timeslider.set_value(position)
                    self.led.SetValue("{:.3f}".format(position))

        else:
            # it was asked to end pausing
            if self.__smmps.is_paused() is True:
                self.play()

    # -----------------------------------------------------------------------

    def stop(self):
        """Stop to play the media."""
        self.__smmps.stop()
        # self.prev_time = None
        self.DeletePendingEvents()
        self.FindWindow("media_pause").SetValue(False)

        # Put the slider exactly at the right time position
        position = self.__smmps.tell()
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))

    # -----------------------------------------------------------------------

    def media_rewind(self):
        """Seek media 10% earlier but no more than the beginning of the period."""
        d = self.__smmps.get_duration()
        d /= 10.
        cur = self.__smmps.tell()
        period = self._timeslider.get_range()

        self.__smmps.seek(max(period[0], cur - d))
        position = self.__smmps.tell()
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))

    # -----------------------------------------------------------------------

    def media_forward(self):
        """Seek media 10% later but no more that the end of the period."""
        duration = self.__smmps.get_duration()
        d = duration / 10.
        cur = self.__smmps.tell()
        period = self._timeslider.get_range()
        position = min(cur + d, period[1])

        # if we reach the end of the stream for the given period
        if position == period[1] and self.IsReplay() is True:
            position = 0.  # restart from the beginning

        self.__smmps.seek(position)
        position = self.__smmps.tell()
        self._timeslider.set_value(position)
        self.led.SetValue("{:.3f}".format(position))

    # -----------------------------------------------------------------------

    def media_seek(self, value):
        """Seek media at given time value inside the period."""
        self.__smmps.seek(value)
        self._timeslider.set_value(value)
        self.led.SetValue("{:.3f}".format(value))

    # -----------------------------------------------------------------------

    def media_period(self, start, end):
        """Override. Set time period to media at given time range."""
        # no need to force to set the period to the media right now because
        # the media will get the period when needed.
        # self.__smmps.set_period(start, end)

        # but a change of period can imply a change of the moment value:
        value = self.__smmps.tell()
        self._timeslider.set_value(value)
        self.led.SetValue("{:.3f}".format(value))

    # -----------------------------------------------------------------------
    # Multi Media Player
    # -----------------------------------------------------------------------

    def add_audio(self, filename):
        """Load the files that filenames refers to.

        The event MediaLoaded or MediaNotLoaded is sent when the audio
        finished to load. Loaded successfully or not, the audio is disabled.

        :param filename: (str) Name of a file or list of file names
        :return: (bool) Always returns False

        """
        self.__smmps.add_audio(filename)
        # The media will send an EVT_MEDIA_XXX when loaded

    # -----------------------------------------------------------------------

    def add_video(self, filename, player=None):
        """Add a video into the list of media managed by this control.

        The new video is disabled.

        :param filename: (str) A filename or a list of file names
        :param player: (wx.Window) a window or a list of wx windows
        :return: (bool)

        """
        self.__smmps.add_video(filename, player)
        # The media will send an EVT_MEDIA_XXX when loaded

    # -----------------------------------------------------------------------

    def add_unsupported(self, filename, duration):
        """Add a file into the list managed by this control.

        :param filename: (str) A filename or a list of file names
        :param duration: (float) Duration of this file
        :return: (bool)

        """
        self.__smmps.add_unsupported(filename, duration)

        # Update the duration of the slider with the longest duration
        duration = self.__smmps.get_duration()
        self._timeslider.set_duration(duration)

    # -----------------------------------------------------------------------

    def add_media(self, media):
        """Add a media into the list of media managed by this control.

        The new media is disabled.

        :param media: (sppasBasePlayer)
        :return: (bool)

        """
        self.__smmps.add_media(media)

    # -----------------------------------------------------------------------

    def enable(self, filename, value=True):
        """Enable or disable the given media.

        When a media is disabled, it can't be paused nor played. It can only
        stay in the stopped state.

        :param filename: (str)
        :param value: (bool)
        :return: (bool)

        """
        self.__smmps.enable(filename, value)

    # -----------------------------------------------------------------------

    def remove(self, filename):
        """Remove a file of the list of media."""
        self.__smmps.remove(filename)

    # -----------------------------------------------------------------------

    def get_duration(self, filename=None):
        """Return the duration this player must consider (in seconds)."""
        return self.__smmps.get_duration(filename)

    def exists(self, filename):
        """Return True if the given filename is matching an existing media."""
        return self.__smmps.exists(filename)

    def is_enabled(self, filename=None):
        """Return True if any media or the given one is enabled."""
        return self.__smmps.is_enabled(filename)

    def is_unknown(self, filename=None):
        """Return True if any media or if the given one is unknown."""
        return self.__smmps.is_unknown(filename)

    def is_audio(self, filename=None):
        """Return True if any media or if the given one is an audio."""
        return self.__smmps.is_audio(filename)

    def is_video(self, filename=None):
        """Return True if any media or if the given one is a video."""
        return self.__smmps.is_video(filename)

    def get_nchannels(self, filename):
        """Return the number of channels."""
        return self.__smmps.get_nchannels(filename)

    def get_sampwidth(self, filename):
        return self.__smmps.get_sampwidth(filename)

    def get_framerate(self, filename):
        return self.__smmps.get_framerate(filename)

    def get_frames(self, filename):
        return self.__smmps.get_frames(filename)

    def get_video_width(self, filename):
        return self.__smmps.get_video_width(filename)

    def get_video_height(self, filename):
        return self.__smmps.get_video_height(filename)

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def _setup_mmpc_events(self):
        """Associate a handler function with the events. """
        # Custom event to inform the media is loaded
        self.__smmps.Bind(MediaEvents.EVT_MEDIA_LOADED, self.__on_media_loaded)
        self.__smmps.Bind(MediaEvents.EVT_MEDIA_NOT_LOADED, self.__on_media_not_loaded)
        # Event received every X ms when the audio is playing
        self.Bind(wx.EVT_TIMER, self.__on_timer)

    # ----------------------------------------------------------------------

    def _on_set_visible(self, event):
        """Change the visible part or other visible contents.

        Scroll the visible part, depending on its current duration:
            - reduce of 50%
            - increase of 100%
            - shift 80% before
            - shift 80% after
        Show or hide annotations, waveform...

        """
        evt_obj = event.GetEventObject()
        # cur_period = self._timeslider.get_range()
        start = self._timeslider.get_visible_start()
        end = self._timeslider.get_visible_end()
        dur = end - start

        if evt_obj.GetName() == "expand_false":
            shift = dur / 4.
            self._timeslider.set_visible_range(start + shift, end - shift)

        elif evt_obj.GetName() == "expand_true":
            shift = dur / 2.
            self._timeslider.set_visible_range(start - shift, end + shift)

        elif evt_obj.GetName() == "scroll_left":
            shift = 0.8 * dur
            if start > 0.:
                self._timeslider.set_visible_range(start - shift, end - shift)

        elif evt_obj.GetName() == "scroll_right":
            shift = 0.8 * dur
            if end < self._timeslider.get_duration():
                self._timeslider.set_visible_range(start + shift, end + shift)

        elif evt_obj.GetName() == "scroll_to_selection":
            sel_start = self._timeslider.get_selection_start()
            sel_end = self._timeslider.get_selection_end()
            sel_middle = sel_start + ((sel_end - sel_start) / 2.)
            shift = dur / 2.
            self._timeslider.set_visible_range(sel_middle - shift, sel_middle + shift)

        elif evt_obj.GetName() == "scroll_zoom_selection":
            sel_start = self._timeslider.get_selection_start()
            sel_end = self._timeslider.get_selection_end()
            self._timeslider.set_visible_range(sel_start, sel_end)

        elif evt_obj.GetName() == "scroll_zoom_all":
            new_end = self.__smmps.get_duration()
            self._timeslider.set_duration(new_end)
            self._timeslider.set_visible_range(0., new_end)

        elif evt_obj.GetName() == "sort":
            self.notify(action="sort_files", value=True)
            return

        elif evt_obj.GetName() == "tier_infos":
            # value = False = show infos
            # value = True = show annotations
            self.notify(action="tiers_annotations", value=evt_obj.GetValue())
            return

        elif evt_obj.GetName() == "sound_wave_lines":
            # value = True = show waveform
            self.notify(action="audio_waveform", value=evt_obj.GetValue())
            return

        else:
            wx.LogError("Unknown visible action {}".format(evt_obj.GetName()))
            return

        self._timeslider.Layout()
        self._timeslider.Refresh()

        # Notify the parent if the visible part has changed.
        new_visible_start = self._timeslider.get_visible_start()
        new_visible_end = self._timeslider.get_visible_end()
        if new_visible_start != start or new_visible_end != end:
            self.notify(action="visible", value=(new_visible_start, new_visible_end))

    # ----------------------------------------------------------------------

    def _on_period_changed(self, event):
        """Override. Handle the event of a change of time range in the slider."""
        p = event.period
        self.media_period(p[0], p[1])
        self._set_led_fg_color()
        self.led.Refresh()

    # ----------------------------------------------------------------------

    def __on_media_loaded(self, event):
        filename = event.filename

        self.__smmps.enable(filename)
        self.FindWindow("media_play").Enable(True)
        self.FindWindow("media_pause").Enable(True)

        # Update the duration of the slider with the longest duration
        duration = self.__smmps.get_duration()
        self._timeslider.set_duration(duration)

        # Under MacOS, the following line enters in an infinite loop with the message:
        #   In file /Users/robind/projects/bb2/dist-osx-py38/build/ext/wxWidgets/src/unix/threadpsx.cpp at line 370: 'pthread_mutex_[timed]lock()' failed with error 0x00000023 (Resource temporarily unavailable).
        # Under Linux it crashes with the message:
        #   pure virtual method called
        self.__smmps.set_period(0., duration)

        wx.PostEvent(self.GetParent(), event)

    # ----------------------------------------------------------------------

    def __on_media_not_loaded(self, event):
        filename = event.filename
        wx.LogError("File {} not loaded".format(filename))
        # self.remove(filename)

    # ----------------------------------------------------------------------

    def __on_timer(self, event):
        # at least one audio is still playing
        if self.__smmps.is_playing() is True:
            # if we doesn't want to update the slider so frequently:
            # cur_time = datetime.datetime.now()
            # delta = cur_time - self.prev_time
            # delta_seconds = delta.seconds + delta.microseconds / 1000000.
            # if delta_seconds > self.delta_slider:
            # self.prev_time = cur_time
            time_pos = self.__smmps.tell()
            self._timeslider.set_value(time_pos)
            self.led.SetValue("{:.3f}".format(time_pos))

        # all enabled audio are now stopped
        elif self.__smmps.are_stopped() is True:
            self.stop()
            if self.IsReplay() is True:
                self.play()

# ---------------------------------------------------------------------------


class TestPanel(sppasPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="SMMPS + Controls")

        button1 = wx.Button(self, -1, size=(100, 50), label="LOAD with threads", name="load_button_1")
        button2 = wx.Button(self, -1, size=(100, 50), label="LOAD sequentially", name="load_button_2")
        self.smmc = sppasMMPCtrl(parent=self)
        self.smmc.SetMinSize(wx.Size(640, 120))

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(button1, 0, wx.ALL, 8)
        s.Add(button2, 0, wx.ALL, 8)
        s.Add(self.smmc, 1, wx.EXPAND)
        self.SetSizer(s)

        button1.Bind(wx.EVT_BUTTON, self._on_load_1)
        button2.Bind(wx.EVT_BUTTON, self._on_load_2)
        self.FindWindow("media_play").Enable(False)

    # ----------------------------------------------------------------------

    def _on_load_1(self, event):
        self.load_files(with_threads=True)

    # ----------------------------------------------------------------------

    def _on_load_2(self, event):
        self.load_files(with_threads=False)

    # ----------------------------------------------------------------------

    def load_files(self, with_threads=True):
        self.FindWindow("load_button_1").Enable(False)
        self.FindWindow("load_button_2").Enable(False)

        # Loading the videos with threads make the app crashing under MacOS:
        # Python[31492:1498940] *** Terminating app due to uncaught exception
        # 'NSInternalInconsistencyException', reason: 'NSWindow drag regions
        # should only be invalidated on the Main Thread!'
        player = sppasImageFrame(
            parent=self,  # if parent is destroyed, the frame will be too
            title="Video",
            style=wx.CAPTION | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.DIALOG_NO_PARENT)

        self.smmc.add_unsupported("a filename of a file", 65.)

        # To load files in parallel, with threads:
        if with_threads is True:
            self.smmc.add_audio(
                [os.path.join(paths.samples, "samples-fra", "F_F_B003-P8.wav"),
                 os.path.join(paths.samples, "samples-fra", "F_F_B003-P9.wav"),
                 os.path.join(paths.samples, "samples-eng", "oriana1.wav"),
                 os.path.join(paths.samples, "samples-eng", "oriana2.WAV"),
                 ])
            self.smmc.add_video([os.path.join(paths.samples, "faces", "video_sample.mp4")], player)

        else:
            # To load files sequentially, without threads:
            self.smmc.add_audio(os.path.join(paths.samples, "samples-fra", "F_F_B003-P8.wav"))
            self.smmc.add_audio(os.path.join(paths.samples, "samples-fra", "F_F_B003-P9.wav"))
            self.smmc.add_audio(os.path.join(paths.samples, "samples-eng", "oriana1.wav"))
            self.smmc.add_audio(os.path.join(paths.samples, "samples-eng", "oriana2.WAV"))
            self.smmc.add_video(os.path.join(paths.samples, "faces", "video_sample.mp4"), player)

        self.smmc.set_visible_range(1., 7.)
        self.smmc.set_selection_range(2., 4.)
