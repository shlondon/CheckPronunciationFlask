"""
:filename: sppas.src.annotations.Intsint.sppasintsint.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the INTSINT automatic annotation.

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

from sppas.src.anndata import sppasTrsRW
from sppas.src.anndata import sppasTranscription
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag

from sppas.src.anndata.anndataexc import AnnDataTypeError
from sppas.src.anndata.anndataexc import AnnDataEqError

from ..annotationsexc import NoTierInputError
from ..baseannot import sppasBaseAnnotation
from ..searchtier import sppasFindTier
from ..autils import SppasFiles

from .intsint import Intsint

# ---------------------------------------------------------------------------


class sppasIntsint(sppasBaseAnnotation):
    """SPPAS integration of the INTSINT automatic annotation.

    """

    def __init__(self, log=None):
        """Create a new instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasIntsint, self).__init__("intsint.json", log)
        self.__intsint = Intsint()

    # -----------------------------------------------------------------------
    # Methods to annotate
    # -----------------------------------------------------------------------

    @staticmethod
    def tier_to_anchors(momel_tier):
        """Initialize INTSINT attributes from a Tier with anchors.

        :param momel_tier: (sppasTier) A PointTier with float values.
        :returns: List of tuples (time, f0 value)

        """
        targets = list()
        for ann in momel_tier:
            # Get the f0 value
            tag = ann.get_best_tag(label_idx=0)
            try:
                f0 = float(tag.get_content())
            except TypeError:
                raise AnnDataTypeError(tag, 'float')
            except ValueError:
                raise AnnDataTypeError(tag, 'float')

            # Get the time value
            try:
                time = float(ann.get_highest_localization().get_midpoint())
            except TypeError:
                raise AnnDataTypeError(ann.get_highest_localization(), 'float')
            except ValueError:
                raise AnnDataTypeError(ann.get_highest_localization(), 'float')

            targets.append((time, f0))

        return targets

    # -------------------------------------------------------------------

    @staticmethod
    def tones_to_tier(tones, anchors_tier):
        """Convert the INTSINT result into a tier.

        :param tones: (list)
        :param anchors_tier: (sppasTier)

        """
        if len(tones) != len(anchors_tier):
            raise AnnDataEqError("tones:"+str(len(tones)), "anchors:"+str(len(anchors_tier)))

        tier = sppasTier("INTSINT")
        for tone, anchor_ann in zip(tones, anchors_tier):
            # Create the label
            tag = sppasTag(tone)
            # Create the location
            location = anchor_ann.get_location().copy()
            # Create the annotation
            tier.create_annotation(location, sppasLabel(tag))

        return tier

    # -----------------------------------------------------------------------

    def get_input_tier(self, input_files):
        """Return the tier with Momel anchors.

        :param input_files: (list)
        :raise: NoTierInputError
        :return: (sppasTier) Tier of type Point

        """
        tier = None
        for filename in input_files:
            parser = sppasTrsRW(filename)
            print(filename)
            trs_input = parser.read()
            for t in trs_input:
                print(t.get_name())
            if tier is None:
                tier = sppasFindTier.pitch_anchors(trs_input)
            if tier is None:
                tier = sppasFindTier.pitch(trs_input)
            if tier is not None:
                break

        # Check input tier
        if tier is None:
            logging.error("Tier with Momel anchors not found.")
            raise NoTierInputError
        if tier.is_point() is False:
            logging.error("The tier with Momel anchors should be of type: Point.")
            raise AnnDataTypeError(tier.get_name(), 'PointTier')

        return tier

    # -----------------------------------------------------------------------
    # Apply the annotation on one given file
    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) momel anchors
        :param output: (str) the output file name
        :returns: (sppasTranscription)

        """
        # Get the tier to be annotated.
        tier_input = self.get_input_tier(input_files)

        # Annotate the tier
        targets = sppasIntsint.tier_to_anchors(tier_input)
        tones = self.__intsint.annotate(targets)
        tier_intsint = sppasIntsint.tones_to_tier(tones, tier_input)

        # Create the transcription result
        trs_output = sppasTranscription(self.name)
        trs_output.set_meta('annotation_result_of', input_files[0])
        trs_output.append(tier_intsint)

        # Save in a file
        if output is not None:
            output_file = self.fix_out_file_ext(output)
            parser = sppasTrsRW(output_file)
            parser.write(trs_output)
            return [output_file]

        return trs_output

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-intsint")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        INTSINT requires momel anchors which can either be stored in
        a TextGrid file or in a PitchTier file.

        :return: (list of list)

        """
        return [SppasFiles.get_informat_extensions("ANNOT")]
