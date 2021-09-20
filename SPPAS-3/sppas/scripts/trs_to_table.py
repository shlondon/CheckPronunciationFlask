#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
:filename: sppas.scripts.trs_to_table.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Export annotated data into time-tables.

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

This script can export annotated files into WEKA file format.
Weka is a collection of machine learning algorithms for data mining tasks.
https://www.cs.waikato.ac.nz/ml/weka/

WEKA is supporting 2 file formats:

    1. ARFF: a simple ASCII file,
    2. XRFF: an XML file which can be compressed with gzip.

This script can export a transcription file into the TRA format of SPPAS:
the Table Rich Annotations format.

"""

import sys
import os.path
from argparse import ArgumentParser
import pickle
import time

PROGRAM = os.path.abspath(__file__)
SPPAS = os.path.dirname(os.path.dirname(os.path.dirname(PROGRAM)))
sys.path.append(SPPAS)

from sppas.src.anndata import sppasTrsRW

# ----------------------------------------------------------------------------
# Verify and extract args:
# ----------------------------------------------------------------------------

parser = ArgumentParser(usage="{:s} -i file [options]"
                              "".format(os.path.basename(PROGRAM)),
                        description="... a script to export annotated files "
                                    "into a table format (tra, arff, xrff).")

parser.add_argument("-i",
                    metavar="file",
                    required=True,
                    help='Input annotated file name')

parser.add_argument("-c",
                    metavar="class",
                    required=False,
                    type=str,
                    help='Name of the tier for the class')

parser.add_argument("-C",
                    metavar="classtags",
                    required=False,
                    type=int,
                    default=10,
                    help='Reduce the maximum number of possible tags of'
                         ' the class (default: 100).')

parser.add_argument("-t",
                    metavar="value",
                    required=False,
                    action='append',
                    type=int,
                    help='An attribute tier number '
                         '(use as many -t options as wanted). '
                         'Positive or negative value: '
                         '1=first tier, -1=last tier.')

parser.add_argument("-n",
                    metavar="tiername",
                    required=False,
                    action='append',
                    type=str,
                    help='An attribute tier name '
                         '(use as many -n options as wanted).')

instance_group = parser.add_mutually_exclusive_group(required=False)

instance_group.add_argument("-a",
                            metavar="anchor",
                            required=False,
                            type=str,
                            help='Name of the anchor tier '
                                 'to create instances.')

instance_group.add_argument("-s",
                            metavar="step",
                            required=False,
                            type=float,
                            help='Time step to create instances.')

parser.add_argument("-u",
                    metavar="uncertaintag",
                    required=False,
                    type=str,
                    default="?",
                    help='Tag that is used into annotations for '
                         'an uncertain label. (default: ?)')

parser.add_argument("-e",
                    metavar="emptytag",
                    required=False,
                    type=str,
                    default="none",
                    help='Tag to be used for un-labelled annotations. '
                         '(default: none)')

parser.add_argument("-E",
                    metavar="emptyclasstag",
                    required=False,
                    type=str,
                    default="none",
                    help='Tag to be used for un-labelled annotations '
                         'in the class. (default: none)')

parser.add_argument("--probas",
                    action='store_true',
                    help="Enable the conversion of annotations into "
                         "distribution of probabilities.")

parser.add_argument("--xra",
                    action='store_true',
                    help="Also export an xra file.")

parser.add_argument("--arff",
                    action='store_true',
                    help="Export into the ARFF file format instead of TRA.")

parser.add_argument("--xrff",
                    action='store_true',
                    help="Export into the XRFF file format instead of TRA.")

parser.add_argument("--quiet",
                    action='store_true',
                    help="Disable the verbosity")

if len(sys.argv) <= 1:
    sys.argv.append('-h')

args = parser.parse_args()

if args.arff and args.xrff:
    print("xrff and arff options can't be used together. Choose only one.")
    sys.exit(1)

# ----------------------------------------------------------------------------
# Read

parser = sppasTrsRW(args.i)

if args.quiet is False:
    print("Read input:")

start_time = time.time()
trs = parser.read(heuristic=True)
end_time = time.time()

if args.quiet is False:
    print("  - elapsed time for reading: {:f} seconds"
          "".format(end_time - start_time))
    pickle_string = pickle.dumps(trs)
    print("  - memory usage of the transcription: {:d} bytes"
          "".format(sys.getsizeof(pickle_string)))

# ----------------------------------------------------------------------------
# Attributes tiers

attribute_type = "string"
if args.probas:
    attribute_type = "numeric"

# Take all tiers or only specified tiers
attribute_tiers = list()
if not args.t and not args.n:
    for tier in trs:
        tier.set_meta("table_attribute", attribute_type)

if args.t:
    for tier_number in args.t:
        if 0 < tier_number <= len(trs):
            trs[tier_number-1].set_meta("table_attribute", attribute_type)
        elif tier_number < 0:
            trs[tier_number].set_meta("table_attribute", attribute_type)
        else:
            print("{:d} is not a valid tier number.".format(tier_number))
            sys.exit(1)

if args.n:
    for tier_name in args.n:
        tier = trs.find(tier_name)
        if tier is not None:
            tier.set_meta("table_attribute", attribute_type)

# ----------------------------------------------------------------------------
# Class

if args.c:
    tier = trs.find(args.c)
    if tier is None:
        print("{:s} is not a valid tier name.".format(args.c))
        sys.exit(1)
    tier.set_meta("table_class", "assigned")
    tier.pop_meta("table_attribute")

# ----------------------------------------------------------------------------
# Time split

if args.a:
    tier = trs.find(args.a)
    if tier is None:
        print("{:s} is not a valid tier name.".format(args.a))
        sys.exit(1)
    tier.set_meta('table_instance_anchor', "")

if args.s:
    trs.set_meta("table_instance_step", str(args.s))

# ----------------------------------------------------------------------------
# Meta-data, to configure how the data will have to be interpreted

if args.e:
    trs.set_meta("table_empty_annotation_tag", args.e)

if args.E:
    trs.set_meta("table_empty_annotation_class_tag", args.E)

if args.u:
    trs.set_meta("table_uncertain_annotation_tag", args.u)

if args.C:
    trs.set_meta("table_max_class_tags", str(args.C))

# ----------------------------------------------------------------------------

name, extension = os.path.splitext(args.i)
fn = name + ".tra"
if args.xrff:
    fn = name + ".xrff"
if args.arff:
    fn = name + ".arff"

parser.set_filename(fn)

# ----------------------------------------------------------------------------
# Write

if args.quiet is False:
    print("Write output file:")

start_time = time.time()
parser.write(trs)
end_time = time.time()

if args.quiet is False:
    print("  - elapsed time for writing: {:f} seconds"
          "".format(end_time - start_time))
    print("Done.")

# XRA
if args.xra:
    parser.set_filename(name + "-export.xra")
    parser.write(trs)
