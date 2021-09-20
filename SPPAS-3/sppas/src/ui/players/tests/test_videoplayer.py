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

    src.ui.players.tests.test_videoplayer.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import unittest
import os.path

from sppas.src.config import paths

from ..videoplayer import sppasSimpleVideoPlayer
from ..videoplayercv import sppasSimpleVideoPlayerCV
from ..videoplayerwx import sppasSimpleVideoPlayerWX

# ---------------------------------------------------------------------------

sample_video = os.path.join(paths.samples, "faces", "video_sample.mp4")

# ---------------------------------------------------------------------------


class TestVideoPlayer(unittest.TestCase):

    def test_load(self):
        """Test in loading multiple audio files."""
        vp = sppasSimpleVideoPlayer()

        loaded = vp.load("toto.video")   # Error 2005 extension not supported
        self.assertTrue(vp.get_filename(), "toto.video")
        self.assertFalse(loaded)
        self.assertTrue(vp.is_unknown())
        self.assertFalse(vp.is_stopped())

        loaded = vp.load(sample_video)
        self.assertTrue(vp.get_filename(), sample_video)
        self.assertTrue(loaded)
        self.assertTrue(vp.is_stopped())
        self.assertFalse(vp.is_audio())
        self.assertTrue(vp.is_video())

    # -----------------------------------------------------------------------

    def test_player_cv(self):
        mp = sppasSimpleVideoPlayerCV()
        mp.load(sample_video)
        mp.play()

    # -----------------------------------------------------------------------

    def test_player_wx(self):
        mp = sppasSimpleVideoPlayerWX()
        mp.load(sample_video)
        mp.play()
