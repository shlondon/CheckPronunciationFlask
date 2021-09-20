#!/usr/bin/env python
"""
:filename: sppas.bin.otherrepetition.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Run the Other-Repetitions automatic annotation.

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
import sys
import os
from argparse import ArgumentParser

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

from sppas import sg, lgs

from sppas.src.annotations import sppasOtherRepet
from sppas.src.annotations import sppasParam
from sppas.src.wkps import sppasWkpRW
from sppas.src.annotations import sppasAnnotationsManager

# ---------------------------------------------------------------------------


if __name__ == "__main__":

    # -----------------------------------------------------------------------
    # Fix initial annotation parameters
    # -----------------------------------------------------------------------

    parameters = sppasParam(["otherrepet.json"])
    ann_step_idx = parameters.activate_annotation("otherrepet")
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
                                        sg.__copyright__, sg.__contact__))

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
        help='Input file name with time-aligned tokens of the main speaker.')

    group_io.add_argument(
        "-s",
        metavar="file",
        help='Input file name with time-aligned tokens of the echoing speaker')

    group_io.add_argument(
        "-w",
        metavar="file",
        help='Workspace file name.')

    group_io.add_argument(
        "-I",
        metavar="file",
        help='Add and check a file into the workspace.')

    group_io.add_argument(
        "-o",
        metavar="file",
        help='Output file name with other-repetitions.')

    group_io.add_argument(
        "-r",
        help='List of stop-words')

    group_io.add_argument(
        "-l",
        metavar="lang",
        choices=parameters.get_langlist(ann_step_idx),
        help='Language code (iso8859-3). One of: {:s}.'
             ''.format(" ".join(parameters.get_langlist(ann_step_idx))))

    group_io.add_argument(
        "-e",
        metavar=".ext",
        default=parameters.get_default_outformat_extension("ANNOT"),
        choices=parameters.get_outformat_extensions("ANNOT"),
        help='Output file extension. One of: {:s}'
             ''.format(" ".join(parameters.get_outformat_extensions("ANNOT"))))

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
        if a not in ('w', 'i', 'I', 'o', 's', 'r', 'l', 'e', 'log', 'quiet'):
            parameters.set_option_value(ann_step_idx, a, str(arguments[a]))
            o = parameters.get_step(ann_step_idx).get_option_by_key(a)

    if args.i and args.w:
        parser.print_usage()
        print("{:s}: error: argument -w: not allowed with argument -i"
              "".format(os.path.basename(PROGRAM)))
        sys.exit(1)

    if args.w:

        if not args.l:
            print("argparse.py: error: option -l is required with option -w")
            sys.exit(1)

        wp = sppasWkpRW(args.w)
        wkp = wp.read()
        parameters.set_workspace(wkp)

        # Fix input files
        if args.I:
            for f in args.I:
                parameters.add_to_workspace(os.path.abspath(f))

        # Fix the output file extension and others
        parameters.set_lang(args.l)
        parameters.set_output_extension(args.e, "ANNOT")
        parameters.set_report_filename(args.log)

        # Perform the annotation
        process = sppasAnnotationsManager()
        process.annotate(parameters)

    elif args.i:

        if not args.s:
            print("argparse.py: error: option -s is required with option -i")
            sys.exit(1)

        # Perform the annotation on a single file
        # ---------------------------------------

        ann = sppasOtherRepet(log=None)
        ann.load_resources(args.r)
        ann.fix_options(parameters.get_options(ann_step_idx))

        if args.o:
            ann.run([args.i, args.s], output=args.o)
        else:
            trs = ann.run([args.i, args.s])
            for tier in trs:
                for a in tier:
                    print("{} {} {:s}".format(
                        a.get_location().get_best().get_begin().get_midpoint(),
                        a.get_location().get_best().get_end().get_midpoint(),
                        a.get_best_tag().get_content()))

    else:

        if not args.quiet:
            print("No file was given to be annotated. Nothing to do!")
