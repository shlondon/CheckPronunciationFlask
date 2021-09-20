# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.ui.players.wxvideoplay.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A player to play a single video file inside a wx frame.

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

A wx.App() must be created first!

"""

import logging
import os
import datetime
import threading
import wx

from sppas.src.config import paths
from sppas.src.ui.phoenix.windows.frame import sppasImageFrame
from sppas.src.ui.phoenix.windows.basedcwindow import sppasImageDCWindow

from .pstate import PlayerState
from .videoplayer import sppasSimpleVideoPlayer

# ---------------------------------------------------------------------------


class sppasSimpleVideoPlayerWX(sppasSimpleVideoPlayer, wx.Timer):
    """A video player based on both cv2 library and wx.

    """

    def __init__(self, owner, player=None):
        """Create an instance of sppasVideoPlayer.

        :param owner: (wx.Window) Owner of this class.

        """
        wx.Timer.__init__(self, owner)
        sppasSimpleVideoPlayer.__init__(self)

        # The delay to set the player bg image while playing
        self._timer_delay = 40    # in milliseconds

        if player is not None:
            try:
                owner = player.GetParent()
                player.SetBackgroundImage(os.path.join(paths.etc, "images", "mire.jpg"))
                player.Show()
                if player.IsShown():
                    player.Hide()
                player.Refresh()
                self._player = player
            except AttributeError:
                wx.LogError("The given video player is not of a compatible "
                            "type. A sppasDCWindows() was expected.")

        if self._player is None:
            # The frame in which images of the video are sent
            self._player = sppasImageFrame(
                parent=owner,   # if owner is destroyed, the frame will be too
                title="Video",
                style=wx.CAPTION | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.DIALOG_NO_PARENT)
            self._player.SetBackgroundColour(wx.WHITE)

    # -----------------------------------------------------------------------

    def __del__(self):
        self.reset()

    # -----------------------------------------------------------------------

    def reset(self):
        """Override. Re-initialize all known data and stop the timer."""
        self.Stop()
        try:
            # The video was not created if the init raised a FeatureException
            sppasSimpleVideoPlayer.reset(self)
        except:
            pass

    # -----------------------------------------------------------------------

    def load(self, filename):
        """Open the file that filename refers to and load a buffer of frames.

        :param filename: (str) Name of a video file
        :return: (bool) True if successfully opened and loaded.

        """
        loaded = sppasSimpleVideoPlayer.load(self, filename)
        # With the following, the app will crash if load() is launch into
        # a thread - tested under MacOS only:
        if loaded is True:
            self._timer_delay = int(1000. * (1. / self.get_framerate()))
            logging.debug("Video {:s} loaded. Timer delay: {:d}"
                          "".format(filename, self._timer_delay))

            if wx.Platform != "__WXMAC__" and self._player is not None:
                # CRASH only under MacOS with the error:
                # *** Terminating app due to uncaught exception 'NSInternalInconsistencyException',
                # reason: 'NSWindow drag regions should only be invalidated on the Main Thread!'
                # terminating with uncaught exception of type NSException

                # we fix an height of 512 and set a proportional width
                ratio = float(self._media.get_height()) / 512.
                width = float(self._media.get_width()) / ratio
                width = int(width)
                self._player.SetSize(wx.Size(width, 512))
                logging.debug("Player size is set to: {}, {}".format(width, 512))

        return loaded

    # -----------------------------------------------------------------------

    def play(self):
        """Override. Start to play the video stream, start the timer.

        :return: (bool) True if the action of playing was performed

        """
        if self._ms in (PlayerState().paused, PlayerState().stopped):
            th = threading.Thread(target=self._play_process, args=())
            self._ms = PlayerState().playing
            if self._player is not None:
                self._player.Show(True)
            self._start_datenow = datetime.datetime.now()
            self.Start(self._timer_delay)
            th.start()
            return True

        return False

    # -----------------------------------------------------------------------

    def pause(self):
        """Override. Pause to play the video, stop the timer.

        :return: (bool) True if the action of stopping was performed

        """
        if self._ms == PlayerState().playing:
            # stop playing
            self.Stop()
            self._ms = PlayerState().stopped
            # seek at the exact moment we stopped to play
            offset = self._media.tell()
            self._from_time = float(offset) / float(self._media.get_framerate())
            # set our state
            self._ms = PlayerState().paused
            return True

        return False

    # -----------------------------------------------------------------------

    def stop(self):
        """Override. Stop to play the video, stop the timer.

        :return: (bool) True if the action of stopping was performed

        """
        if self._player.IsShown():
            self._player.Hide()
            self._ms = PlayerState().stopped
            self._media.seek(0)
            self.Stop()
            return True
        return False

    # -----------------------------------------------------------------------
    # Manage events
    # -----------------------------------------------------------------------

    def Notify(self):
        """Override. Notify the owner of the EVT_TIMER event.

        Manage the current position in the audio stream.

        """
        # Nothing to do if we are not playing
        if self._ms == PlayerState().playing:
            if self._current_image is not None:
                # Refresh the video frame
                self._player.SetBackgroundImageArray(self._current_image)
                self._player.Refresh()

# ---------------------------------------------------------------------------


class TestPanel(wx.Panel):
    def __init__(self, parent):
        super(TestPanel, self).__init__(
            parent, -1, style=wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN, name="Simple VideoPlayer WX")

        # Actions to perform with the player
        btn_panel = wx.Panel(self, name='btn_panel')
        btn2 = wx.Button(btn_panel, -1, "Play", name="btn_play")
        self.Bind(wx.EVT_BUTTON, self._on_play_ap, btn2)
        btn3 = wx.Button(btn_panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self._on_pause_ap, btn3)
        btn4 = wx.Button(btn_panel, -1, "Stop")
        self.Bind(wx.EVT_BUTTON, self._on_stop_ap, btn4)
        sizer = wx.BoxSizer()
        sizer.Add(btn2, 0, wx.ALL, 4)
        sizer.Add(btn3, 0, wx.ALL, 4)
        sizer.Add(btn4, 0, wx.ALL, 4)
        btn_panel.SetSizer(sizer)

        img_panel = wx.Panel(self, name="img_panel")
        wi = sppasImageDCWindow(img_panel, name="img_window")
        wi.SetBorderWidth(2)
        self.ap = sppasSimpleVideoPlayerWX(owner=self, player=wi)
        sizer = wx.BoxSizer()
        sizer.Add(wi, 1, wx.EXPAND)
        img_panel.SetSizer(sizer)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(btn_panel, 0, wx.EXPAND)
        main_sizer.Add(img_panel, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        self.Layout()

        wx.CallAfter(self._do_load_file)

    # ----------------------------------------------------------------------

    def _do_load_file(self):
        self.ap.load(os.path.join(paths.samples, "faces", "video_sample.mp4"))
        w = self.ap.get_width()
        h = self.ap.get_height()
        self.FindWindow("img_window").SetSize(wx.Size(w, h))
        logging.debug("Video size: {}x{}".format(w, h))
        self.Refresh()

    # ----------------------------------------------------------------------

    def _on_play_ap(self, event):
        if self.ap.is_paused() is False:
            self.ap.prepare_play(0., self.ap.get_duration())
        self.ap.play()

    # ----------------------------------------------------------------------

    def _on_pause_ap(self, event):
        self.ap.pause()

    # ----------------------------------------------------------------------

    def _on_stop_ap(self, event):
        self.ap.stop()
