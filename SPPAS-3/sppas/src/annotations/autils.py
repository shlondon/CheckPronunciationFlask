# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.autils.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Utility classes for the automatic annotations.

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

from sppas.src.config import annots
from sppas.src.anndata import sppasTrsRW
from sppas.src.imgdata import image_extensions
from sppas.src.audiodata.aio import extensions as audio_extensions
from sppas.src.videodata import video_extensions

# ---------------------------------------------------------------------------


class SppasFiles:

    # All the extensions, for all filetypes
    DEFAULT_EXTENSIONS = dict()
    DEFAULT_EXTENSIONS["ANNOT"] = annots.annot_extension
    DEFAULT_EXTENSIONS["ANNOT_ANNOT"] = annots.annot_extension
    DEFAULT_EXTENSIONS["ANNOT_MEASURE"] = annots.measure_extension
    DEFAULT_EXTENSIONS["ANNOT_TABLE"] = annots.table_extension
    DEFAULT_EXTENSIONS["IMAGE"] = annots.image_extension
    DEFAULT_EXTENSIONS["VIDEO"] = annots.video_extension
    DEFAULT_EXTENSIONS["AUDIO"] = annots.audio_extension

    # The filetypes for created files,
    # none of the current annotations is creating an audio file
    OUT_FORMATS = ("ANNOT", "IMAGE", "VIDEO")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_default_extension(filetype_format):
        """Return the default extension defined for a given format.

        :param filetype_format: (str)
        :return: (str) Extension with the dot or empty string

        """
        if filetype_format in list(SppasFiles.DEFAULT_EXTENSIONS.keys()):
            return SppasFiles.DEFAULT_EXTENSIONS[filetype_format]

        return ""

    # -----------------------------------------------------------------------

    @staticmethod
    def get_informat_extensions(filetype_format):
        """Return the list of input extensions a format can support.

        :param filetype_format: (str)
        :return: (list) Extensions, starting with the dot.

        """
        if filetype_format == "ANNOT":
            all_ext_in = sppasTrsRW.extensions_in()
            return ["." + e for e in all_ext_in]

        if filetype_format == "ANNOT_ANNOT":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.annot_extensions()
            # all extensions with a writer
            all_ext_in = sppasTrsRW.extensions_in()
            # return a AND of both previous lists, add the dot to each extension
            return ["." + e for e in annot_ext if e in all_ext_in]

        if filetype_format == "ANNOT_MEASURE":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.measure_extensions()
            # all extensions with a writer
            all_ext_in = sppasTrsRW.extensions_in()
            # return a AND of both previous lists, add the dot to each extension
            return ["." + e for e in annot_ext if e in all_ext_in]

        if filetype_format == "ANNOT_TABLE":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.table_extensions()
            # all extensions with a writer
            all_ext_in = sppasTrsRW.extensions_in()
            return ["." + e for e in annot_ext if e in all_ext_in]

        if filetype_format == "IMAGE":
            return image_extensions

        if filetype_format == "VIDEO":
            return video_extensions

        if filetype_format == "AUDIO":
            return audio_extensions

        logging.warning("Unknown filetype format: {}. Expected one of: {}."
                        "".format(filetype_format, annots.typeformat))
        return list()

    # -----------------------------------------------------------------------

    @staticmethod
    def get_outformat_extensions(filetype_format):
        """Return the list of output extensions an out_format can support.

        :param filetype_format: (str)
        :return: (list) Extensions, starting with the dot.

        """
        if filetype_format == "ANNOT":
            all_ext_in = sppasTrsRW.extensions_in()
            return ["." + e for e in all_ext_in]

        if filetype_format == "ANNOT_ANNOT":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.annot_extensions()
            # all extensions with a writer
            all_ext_out = sppasTrsRW.extensions_out()
            return ["." + e for e in annot_ext if e in all_ext_out]

        if filetype_format == "ANNOT_MEASURE":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.measure_extensions()
            # all extensions with a writer
            all_ext_out = sppasTrsRW.extensions_out()
            return ["." + e for e in annot_ext if e in all_ext_out]

        if filetype_format == "ANNOT_TABLE":
            # all extension of annotation files (neither measure nor table)
            annot_ext = sppasTrsRW.table_extensions()
            # all extensions with a writer
            all_ext_out = sppasTrsRW.extensions_out()
            return ["." + e for e in annot_ext if e in all_ext_out]

        if filetype_format == "IMAGE":
            return image_extensions

        if filetype_format == "VIDEO":
            return video_extensions

        if filetype_format == "AUDIO":
            return audio_extensions

        return list()
