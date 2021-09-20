#!/usr/bin/env python
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

    scripts.vid_to_img.py
    ~~~~~~~~~~~~~~~~~~~~~

:author:       Brigitte Bigi
:organization: Laboratoire Parole et Langage, Aix-en-Provence, France
:contact:      develop@sppas.org
:license:      GPL, v3
:copyright:    Copyright (C) 2011-2020  Brigitte Bigi
:summary:      a script to create a folder of images from a video

"""

import sys
import os
from argparse import ArgumentParser

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

from sppas.src.config import sppasLogSetup
from sppas.src.videodata.videoutils import video_to_images


# ----------------------------------------------------------------------------
# Verify and extract args:
# ----------------------------------------------------------------------------

parser = ArgumentParser(usage="{:s} -i folder [options]"
                              "".format(os.path.basename(PROGRAM)),
                        description="... a script to create a video from a"
                                    "folder of images.")

parser.add_argument("-i",
                    metavar="file",
                    required=True,
                    help='Input video file')

parser.add_argument("-o",
                    metavar="folder",
                    required=False,
                    help='Output folder name')

if len(sys.argv) <= 1:
    sys.argv.append('-h')

args = parser.parse_args()

# ----------------------------------------------------------------------------

if os.path.exists(args.i) is False:
    print("File {:s} does not exists.".format(args.i))
    sys.exit(1)

if args.o:
    folder = args.o
else:
    folder, _ = os.path.splitext(args.i)

if os.path.exists(folder) is False:
    os.mkdir(folder)
else:
    print("Output folder {} is already existing. "
          "Delete it first.".format(folder))

lgs = sppasLogSetup(0)
lgs.stream_handler()

video_to_images(args.i, folder)

