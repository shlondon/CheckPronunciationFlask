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

    scripts.img_to_vid.py
    ~~~~~~~~~~~~~~~~~~~~~

:author:       Brigitte Bigi
:organization: Laboratoire Parole et Langage, Aix-en-Provence, France
:contact:      develop@sppas.org
:license:      GPL, v3
:copyright:    Copyright (C) 2011-2020  Brigitte Bigi
:summary:      a script to create a video from a folder of images

"""

import sys
import logging
import os
from argparse import ArgumentParser

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

from sppas.src.videodata.videoutils import sppasImageVideoWriter
from sppas.src.config import sppasLogSetup


# ----------------------------------------------------------------------------
# Verify and extract args:
# ----------------------------------------------------------------------------

parser = ArgumentParser(usage="{:s} -i folder [options]"
                              "".format(os.path.basename(PROGRAM)),
                        description="... a script to create a video from a"
                                    "folder of images.")

parser.add_argument("-i",
                    metavar="folder",
                    required=True,
                    help='Input folder with image files')

parser.add_argument("-o",
                    metavar="file",
                    required=False,
                    help='Output video file name')

parser.add_argument("-m",
                    metavar="mul",
                    required=False,
                    default=1,
                    type=int,
                    help='Number of times each image is written in the video (default: 1)')

parser.add_argument("-r",
                    metavar="repeat",
                    required=False,
                    default=1,
                    type=int,
                    help='Number of times each to repeat the sequence of images (default: 1)')

parser.add_argument("-f",
                    metavar="fps",
                    required=False,
                    default=25.,
                    type=float,
                    help='FPS - frame per seconds (default: 25)')

parser.add_argument("--quiet",
                    action='store_true',
                    help="Disable the verbosity.")

if len(sys.argv) <= 1:
    sys.argv.append('-h')

args = parser.parse_args()

# ----------------------------------------------------------------------------

if os.path.exists(args.i) is False:
    print("Folder {:s} does not exists.".format(args.i))
    sys.exit(1)

if args.o:
    video_filename = args.o
else:
    video_filename = os.path.join(args.i, "video.mp4")

if not args.quiet:
    lgs = sppasLogSetup(0)
else:
    lgs = sppasLogSetup(30)
lgs.stream_handler()

# Create a video writer with the images folder as parameter
vidw = sppasImageVideoWriter(args.i)
vidw.set_resolution("HD")  # one of: LD SD HD WFHD UHD WQHD DFHD 4K
vidw.set_aspect("extend")  # one of: center stretch extend zoom

# Configure the video writer
vidw.set_fps(args.f)
logging.debug(" ... fps: {:d}".format(args.f))
vidw.img_mul(args.m)
logging.debug(" ... write each image {:d} times".format(args.m))
vidw.repeat(args.r)
logging.debug(" ... repeat {:d} times the sequence of images".format(args.r))

# Write the video
vidw.export(video_filename)

