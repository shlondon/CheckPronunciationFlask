# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.Activity.sppasactivity.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of Activity automatic annotation

.. _This file is part of SPPAS: <http://www.sppas.org/>
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
import logging

from sppas.src.config import info, annots
from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription, sppasTier
from sppas.src.anndata import sppasLabel, sppasTag, sppasLocation

from ..baseannot import sppasBaseAnnotation
from ..annotationsexc import AnnotationOptionError
from ..searchtier import sppasFindTier
from ..annotationsexc import NoTierInputError
from .activity import Activity

# ---------------------------------------------------------------------------

MSG_EXTRA_TIER = (info(1270, "annotations"))

# ---------------------------------------------------------------------------


class sppasActivity(sppasBaseAnnotation):
    """SPPAS integration of the Activity generation.

    """

    def __init__(self, log=None):
        """Create a new sppasActivity instance.

        :param log: (sppasLog) Human-readable logs.

        """
        sppasBaseAnnotation.__init__(self, "activity.json", log)
        self.__activity = Activity()

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        Available options are:

            - duration

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()

            if "duration" == key:
                self.set_duration_tier(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------

    def set_duration_tier(self, value):
        """Fix the activity duration option.

        :param value: (bool) Activity tier generation.

        """
        self._options['duration'] = bool(value)

    # -----------------------------------------------------------------------
    # Automatic annotation
    # -----------------------------------------------------------------------

    def convert(self, tier, tmin, tmax):
        """Create an Activity and ActivityDuration tier.

        :param tier: (sppasTier)
        :param tmin: (sppasPoint)
        :param tmax: (sppasPoint)
        :returns: (sppasTier, sppasTier)

        """
        try:
            activity = self.__activity.get_tier(tier, tmin, tmax)
        except Exception as e:
            self.logfile.print_message(
                MSG_EXTRA_TIER.format(
                    tiername="Activity", message=str(e)),
                    indent=2, status=annots.warning)
            return None, None

        duration = None
        if self._options['duration'] is True:
            duration = sppasTier('ActivityDuration')
            for a in activity:
                interval = a.get_location().get_best()
                dur = round(interval.duration().get_value(), 6)
                duration.create_annotation(
                    sppasLocation(interval.copy()),
                    sppasLabel(sppasTag(dur, tag_type="float"))
                )

        return activity, duration

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the the tier with aligned tokens.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (sppasTier)

        """
        tier = None
        annot_ext = self.get_input_extensions()

        for filename in input_files:
            fn, fe = os.path.splitext(filename)

            if tier is None and fe in annot_ext[0]:
                parser = sppasTrsRW(filename)
                trs_input = parser.read()
                tier = sppasFindTier.aligned_tokens(trs_input)
                if tier is not None:
                    tmin = trs_input.get_min_loc()
                    tmax = trs_input.get_max_loc()
                    return tier, tmin, tmax

        # Check input tier
        logging.error("Tier with time-aligned tokens not found.")
        raise NoTierInputError

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        Important: options could be changed!

        :param input_files: (list of str) Time-aligned tokens
        :param output: (str) the output name - either filename or basename
        :returns: (sppasTranscription)

        """
        tok_tier, tmin, tmax = self.get_inputs(input_files)
        activity, duration = self.convert(tok_tier, tmin, tmax)

        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        trs_output.append(activity)
        if duration is not None:
            trs_output.append(duration)

        # Save results
        if output is not None:
            output_file = self.fix_out_file_ext(output)
            parser = sppasTrsRW(output_file)
            parser.write(trs_output)
            return [output_file]

        return trs_output

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """List of patterns this annotation expects for its input filenames."""
        return [self._options.get("inputpattern", '-palign')]

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-activity")
