#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
:filename: sppas.bin.facedetection.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Run the dutomatic detections of faces in an image annotation.

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

import logging
import sys
import os
from argparse import ArgumentParser

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

from sppas import sg, lgs

from sppas.src.annotations import sppasFaceDetection
from sppas.src.annotations import sppasParam
from sppas.src.annotations import sppasAnnotationsManager

# ---------------------------------------------------------------------------


if __name__ == "__main__":

    # -----------------------------------------------------------------------
    # Fix initial annotation parameters
    # -----------------------------------------------------------------------

    parameters = sppasParam(["facedetect.json"])
    ann_step_idx = parameters.activate_annotation("facedetect")
    if ann_step_idx == -1:
        print("The automatic annotation can't be enabled.")
        sys.exit(1)
    ann_options = parameters.get_options(ann_step_idx)

    # -----------------------------------------------------------------------
    # Verify and extract args:
    # -----------------------------------------------------------------------

    parser = ArgumentParser(
        usage="%(prog)s [files] [options]",
        description=
        parameters.get_step_name(ann_step_idx) + ": " +
        parameters.get_step_descr(ann_step_idx),
        epilog="This program is part of {:s} version {:s}. {:s}. Contact the "
               "author at: {:s}".format(sg.__name__, sg.__version__,
                                        sg.__copyright__, sg.__contact__)
    )

    parser.add_argument(
        "--quiet",
        action='store_true',
        help="Disable the verbosity")

    parser.add_argument(
        "--log",
        metavar="file",
        help="File name for a Procedure Outcome Report (default: None)")

    # Add arguments for input/output files
    # ------------------------------------

    group_io = parser.add_argument_group('Files')

    group_io.add_argument(
        "-i",
        metavar="file",
        help='Input image.')

    group_io.add_argument(
        "-o",
        metavar="file",
        help='Output base name.')

    group_io.add_argument(
        "-I",
        metavar="file",
        action='append',
        help='Input file name (append).')

    group_io.add_argument(
        "-r",
        metavar="model",
        action='append',
        help='Model base name (as many .caffemodel or .xml models as wishes)')

    group_io.add_argument(
        "-e",
        metavar=".ext",
        default=parameters.get_default_outformat_extension("IMAGE"),
        choices=parameters.get_outformat_extensions("IMAGE"),
        help='Output file extension. One of: {:s}'
             ''.format(" ".join(parameters.get_outformat_extensions("IMAGE"))))

    # Add arguments from the options of the annotation
    # ------------------------------------------------

    group_opt = parser.add_argument_group('Options')
    for opt in ann_options:
        group_opt.add_argument(
            "--" + opt.get_key(),
            type=opt.type_mappings[opt.get_type()],
            default=opt.get_value(),
            help=opt.get_text() + " (default: {:s})"
                                  "".format(opt.get_untypedvalue()))

    # Force to print help if no argument is given then parse
    # ------------------------------------------------------

    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    args = parser.parse_args()

    # Mutual exclusion of inputs
    # --------------------------

    if args.i and args.I:
        parser.print_usage()
        print("{:s}: error: argument -I: not allowed with argument -i"
              "".format(os.path.basename(PROGRAM)))
        sys.exit(1)

    # -----------------------------------------------------------------------
    # The automatic annotation is here:
    # -----------------------------------------------------------------------

    # Redirect all messages to logging
    # --------------------------------

    if args.quiet:
        lgs.set_log_level(30)

    # Get options from arguments
    # --------------------------

    arguments = vars(args)
    for a in arguments:
        if a not in ('i', 'o', 'r', 'e', 'I', 'quiet', 'log'):
            parameters.set_option_value(ann_step_idx, a, str(arguments[a]))

    if args.i:

        # Perform the annotation on a single file
        # ---------------------------------------

        if not args.r:
            print("argparse.py: error: option -r is required with option -i")
            sys.exit(1)

        ann = sppasFaceDetection(log=None)
        ann.load_resources(args.r[0], *args.r[1:])
        ann.fix_options(parameters.get_options(ann_step_idx))

        if args.o:
            ann.run([args.i], output=args.o)
        else:
            coords = ann.run([args.i])
            for c in coords:
                print(c)

    elif args.I:

        # Perform the annotation on a set of files
        # ----------------------------------------

        # Fix input files
        files = list()
        for f in args.I:
            parameters.add_to_workspace(os.path.abspath(f))
            logging.info("File {:s} added to the workspace.".format(f))

        process = sppasAnnotationsManager()

        # Fix the output file extension and others
        parameters.set_report_filename(args.log)
        parameters.set_output_extension(args.e, "IMAGE")

        # Perform the annotation
        process.annotate(parameters)
