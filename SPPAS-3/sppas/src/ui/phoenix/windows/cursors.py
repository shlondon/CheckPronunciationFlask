# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.windows.cursors.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  XPM data of some cursors.

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

import wx

# ---------------------------------------------------------------------------


stretch_cursor_32 = [
"32 32 3 1",
"#	c #000000",
"+	c #FFFFFF",
"                                ",
"                                ",
"                                ",
"               +++            ..",
"               +#+            ..",
"               +#+            ..",
"               +#+            ..",
"       +++++++++#+++++++++    ..",
"       +#################+    ..",
"       +#+++++++#+++++++#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"   +++++#+++++++#+++++++##++++..",
"   +#########################+..",
"   +++++#+++++++#+++++++#+++++..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+    .+#+    .+#+    ..",
"       +#+++++++#+++++++#+    ..",
"       +#################+    ..",
"       +++++++++#+++++++++    ..",
"               +#+            ..",
"               +#+            ..",
"               +#+            ..",
"               +++            ..",
"                                ",
"                                "
]

# from: https://github.com/piksels-and-lines-orchestra/inkscape/tree/master/src/pixmaps
arrow_top_left_cursor_32 = [
"32 32 3 1",
" 	c None",
".	c #FFFFFF",
"+	c #000000",
" ..                             ",
".++..                           ",
".+ ++..                         ",
" .+  ++..                       ",
" .+    ++..                     ",
"  .+     ++.                    ",
"  .+       +.                   ",
"   .+      +.                   ",
"   .+     +.                    ",
"    .+     +.                   ",
"    .+  +   +.                  ",
"     .++.+   +.                 ",
"      .. .+   +.                ",
"          .+   +.               ",
"           .+   +.              ",
"            .+   +.             ",
"             .+   +.            ",
"              .+ +.             ",
"               .+.              ",
"                .               ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                "
]

zoom_in_cursor_32 = [
"32 32 3 1",
" 	c None",
".	c #FFFFFF",
"+	c #000000",
"     ...                        ",
"   ..+++..                      ",
"  .++   ++.                     ",
" .+       +.                    ",
" .+  .+.  +.                    ",
".+  ..+..  +.                   ",
".+  +++++  +.                   ",
".+  ..+..  +.                   ",
" .+  .+.  +.                    ",
" .+       +.                    ",
"  .++   ++.+..                  ",
"   ..+++..+.++.                 ",
"     ...  .+  +.                ",
"          .+   +.               ",
"           .+   +.              ",
"            .+   +.             ",
"             .+   +.            ",
"              .+  +.            ",
"               .++.             ",
"                ..              ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                "
]

zoom_out_cursor_32 = [
"32 32 3 1",
" 	c None",
".	c #FFFFFF",
"+	c #000000",
"     ...                        ",
"   ..+++..                      ",
"  .++   ++.                     ",
" .+       +.                    ",
" .+       +.                    ",
".+  .....  +.                   ",
".+  +++++  +.                   ",
".+  .....  +.                   ",
" .+       +.                    ",
" .+       +.                    ",
"  .++   ++.+..                  ",
"   ..+++..+.++.                 ",
"     ...  .+  +.                ",
"          .+   +.               ",
"           .+   +.              ",
"            .+   +.             ",
"             .+   +.            ",
"              .+  +.            ",
"               .++.             ",
"                ..              ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                ",
"                                "
]

# ---------------------------------------------------------------------------


class sppasCursor():
    """Create a wx.Cursor from raw XPM data.

    """

    def __init__(self, xpmdata, hotspot=16):
        """Create a new instance.

        :param xpmdata: (list of bytes)
        :param hotspot: (int)

        """
        # get XPM data in ASCII, not unicode
        xpmdata_byte = list()
        for line in xpmdata:
            xpmdata_byte.append(line.encode("ASCII"))

        # get cursor image
        self.__image = wx.Bitmap(xpmdata_byte).ConvertToImage()

        # since this image didn't come from a .cur file,
        # tell it where the hotspot is
        self.__image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_X, hotspot)
        self.__image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, hotspot)

    # -----------------------------------------------------------------------

    def create(self, height=None):
        """Return a wx.Cursor from a vectorized image.

        :return: (wx.Cursor)

        """
        image = self.__image

        # resize
        if height is not None and height != self.__image.GetHeight():
            proportion = float(height) / float(self.__image.GetHeight())
            w = int(float(self.__image.GetWidth()) * proportion)
            image.Rescale(w, height, wx.IMAGE_QUALITY_HIGH)

        # make the image into a cursor
        return wx.Cursor(image)
