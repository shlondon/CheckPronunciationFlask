# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_editor.timeline.audioview_risepanel.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  View panel for an audio file.

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
import wx.lib

from sppas.src.config import paths
from sppas.src.audiodata.aio import open as audio_open

from sppas.src.ui.phoenix.windows import sppasScrolledPanel

from .timedatatype import TimelineType
from .baseview_risepanel import sppasFileViewPanel
from .audiovista import sppasAudioVista

# ---------------------------------------------------------------------------


class AudioViewPanel(sppasFileViewPanel):
    """A panel to display the content of an audio.

    The object embedded in this class is a sppasAudioVista.

    Events emitted by this class is EVT_TIME_VIEW:
        - action="close" to ask for closing the panel
        - action="media_loaded", value=boolean to inform the file was
        successfully or un-successfully loaded.

    """

    # -----------------------------------------------------------------------
    # List of accepted percentages of zooming
    ZOOMS = (25, 50, 75, 100, 125, 150, 200, 250, 300, 400)

    # -----------------------------------------------------------------------

    def __init__(self, parent, filename, name="audioview_risepanel"):
        """Create an AudioViewPanel.

        :param parent: (wx.Window) Parent window must NOT be none
        :param filename: (str) The name of the file of the media
        :param name: (str) the widget name.

        """
        super(AudioViewPanel, self).__init__(parent, filename, name)
        self._ft = TimelineType().audio
        self._setup_events()
        self.Collapse()

        self._rgb1 = (220, 225, 250)
        self._rgb2 = (230, 240, 255)
        self.SetRandomColours()

    # -----------------------------------------------------------------------

    def media_zoom(self, direction):
        """Zoom the child.

        :param direction: (int) -1 to zoom out, +1 to zoom in and 0 to reset
        to the initial size.

        """
        if self.IsExpanded() is False:
            return

        if direction == 0:
            self.GetPane().SetZoom(100)
        else:
            idx_zoom = AudioViewPanel.ZOOMS.index(self.GetPane().GetZoom())
            if direction < 0:
                new_idx_zoom = max(0, idx_zoom-1)
            else:
                new_idx_zoom = min(len(AudioViewPanel.ZOOMS)-1, idx_zoom+1)
            self.GetPane().SetZoom(AudioViewPanel.ZOOMS[new_idx_zoom])

        self.update_ui()

    # -----------------------------------------------------------------------

    def show_waveform(self, value):
        """Enable or disable the waveform.

        If the waveform is enabled, the infos are automatically disabled.

        """
        self.GetPane().show_waveform(value)
        # Automatically enable infos if nothing else is enabled
        if value is False:
            if self.GetPane().infos_shown() is False:
                self.GetPane().show_infos(True)
        # and automatically disable infos if something else is enabled
        else:
            if self.GetPane().infos_shown() is True:
                self.GetPane().show_infos(False)

    # -----------------------------------------------------------------------
    # Construct the GUI
    # -----------------------------------------------------------------------

    def _create_content(self):
        """Override. Create the content of the panel."""
        self.AddButton("close")

        mc = sppasAudioVista(self)
        mc.SetBackgroundColour(self.GetBackgroundColour())
        mc.SetForegroundColour(self.GetForegroundColour())
        mc.show_infos(True)
        mc.show_waveform(False)
        self.SetPane(mc)
        self.media_zoom(0)  # 100% zoom = initial size

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        self.Bind(wx.EVT_BUTTON, self.__process_tool_event)

    # -----------------------------------------------------------------------

    def __process_tool_event(self, event):
        """Process a button event from the tools.

        :param event: (wx.Event)

        """
        obj = event.GetEventObject()
        name = obj.GetName()
        if name == "close":
            self.notify("close")
        else:
            event.Skip()

# ---------------------------------------------------------------------------


class TestPanel(sppasScrolledPanel):
    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, name="AudioView RisePanel")
        s = wx.BoxSizer(wx.VERTICAL)

        samples = [
            os.path.join(paths.samples, "samples-fra", "F_F_B003-P8.wav"),
            os.path.join(paths.samples, "samples-eng", "oriana1.wav"),
            os.path.join(paths.samples, "samples-eng", "oriana3.wave")
        ]

        for filename in samples:
            panel = AudioViewPanel(self, filename)

            audio = audio_open(filename)
            panel.GetPane().set_audio_data(
                nchannels=audio.get_nchannels(),
                sampwidth=audio.get_sampwidth(),
                framerate=audio.get_framerate(),
                duration=audio.get_duration(),
                frames=audio.read_frames(audio.get_nframes()))
            panel.GetPane().set_visible_period(0., audio.get_duration())
            panel.show_waveform(True)
            panel.Expand()
            s.Add(panel, 0, wx.EXPAND | wx.TOP, 2)

        self.SetSizer(s)
        self.SetupScrolling(scroll_x=False, scroll_y=True)
