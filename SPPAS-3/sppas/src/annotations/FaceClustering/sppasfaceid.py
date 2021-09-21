# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.sppasfaceid.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of FaceClustering automatic annotation

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

from ..annotationsexc import AnnotationOptionError
from ..baseannot import sppasBaseAnnotation
from ..autils import SppasFiles
from ..annotationsexc import NoInputError

from .identifycoords import VideoCoordsIdentification
from .kidswriter import sppasKidsVideoWriter

# ---------------------------------------------------------------------------


class sppasFaceIdentifier(sppasBaseAnnotation):
    """SPPAS integration of the automatic video coordinates identification.

    Requires both an image/video and a CSV file with face coordinates.

    """

    def __init__(self, log=None):
        """Create a new sppasFaceIdentifier instance.

        :param log: (sppasLog) Human-readable logs.

        """
        super(sppasFaceIdentifier, self).__init__("faceidentity.json", log)

        # The objects to store the input data and the results
        self.__video_writer = sppasKidsVideoWriter()

        # The annotator
        self.__pfv = VideoCoordsIdentification()

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "fdmin":
                self.set_fd_threshold(opt.get_value())

            elif key == "ident":
                self.set_ident_export(opt.get_value())

            elif key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "folder":
                self.set_out_folder(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "crop":
                self.set_img_crop(opt.get_value())

            elif key == "width":
                self.set_img_width(opt.get_value())

            elif key == "height":
                self.set_img_height(opt.get_value())

            elif "pattern" in key:
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # ----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    def set_ident_export(self, value):
        """Set the export of a video/csv file for each identified person.

        :param value: (bool) True to export video/csv files

        """
        self.__pfv.set_out_ident(value)

    # -----------------------------------------------------------------------

    def set_fd_threshold(self, value):
        """Threshold to FD confidence to assign a person to a face.

        :param value: (float) fd score

        """
        value = float(value)
        self.__pfv.set_ident_min_confidence(value)
        self._options["fdmin"] = value

    # -----------------------------------------------------------------------

    def set_out_csv(self, out_csv=False):
        """The result includes a CSV file.

        :param out_csv: (bool) Create a CSV file when detecting

        """
        self.__video_writer.set_options(csv=out_csv)
        self._options["csv"] = out_csv

    # -----------------------------------------------------------------------

    def set_out_folder(self, out_folder=False):
        """The result includes a folder with image files.

        :param out_folder: (bool) Create a folder with image files when detecting

        """
        self.__video_writer.set_options(folder=out_folder)
        self._options["folder"] = out_folder

    # -----------------------------------------------------------------------

    def set_img_tag(self, value=True):
        """Surround the faces with a square.

        :param value: (bool) Tag the images

        """
        self.__video_writer.set_options(tag=value)
        self._options["tag"] = value

    # -----------------------------------------------------------------------

    def set_img_crop(self, value=True):
        """Create an image/video for each detected person.

        :param value: (bool) Crop the images

        """
        self.__video_writer.set_options(crop=value)
        self._options["crop"] = value

    # -----------------------------------------------------------------------

    def set_img_width(self, value):
        """Width of the resulting images/video.

        :param value: (int) Number of pixels

        """
        self.__video_writer.set_options(width=value)
        self._options["width"] = value

    # -----------------------------------------------------------------------

    def set_img_height(self, value):
        """Height of the resulting images/video.

        :param value: (int) Number of pixel

        """
        self.__video_writer.set_options(height=value)
        self._options["height"] = value

    # -----------------------------------------------------------------------

    def get_inputs(self, input_files):
        """Return the media and the csv filenames.

        :param input_files: (list)
        :raise: NoInputError
        :return: (str, str) Names of the 2 expected files

        """
        ext = self.get_input_extensions()
        media_ext = ext[0]
        csv_ext = ext[1]
        media = None
        csv = None
        for filename in input_files:
            fn, fe = os.path.splitext(filename)

            if media is None and fe in media_ext:
                # The video or the image is found.
                media = filename
            elif csv is None and fe.lower() in csv_ext:
                csv = filename

        if media is None:
            logging.error("No video was found.")
            raise NoInputError

        if csv is None:
            logging.error("The CSV file with faces was not found.")
            raise NoInputError

        return media, csv

    # -----------------------------------------------------------------------

    def run(self, input_files, output=None):
        """Run the automatic annotation process on an input.

        :param input_files: (list of str) (video ) Video file, CSV file with coords of faces
        :param output: (str) the output base name for files
        :returns: (list) Either the list of list of detected faces or the list
        of all created files.

        """
        # Get and open the video filename from the input
        video_file, csv_file = self.get_inputs(input_files)
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])

        # Assign a person identity to the faces
        if output.endswith(self.get_output_pattern()):
            output = output[:-len(self.get_output_pattern())]

        result = self.__pfv.video_identity(video_file, csv_file, self.__video_writer, output)
        self.__video_writer.close()

        return result

    # -----------------------------------------------------------------------

    def get_input_patterns(self):
        """Patterns this annotation expects for its input filenames.

        """
        return [
            self._options.get("inputpattern", ""),
            self._options.get("inputoptpattern", '-face')
            ]

    # -----------------------------------------------------------------------

    def get_output_pattern(self):
        """Pattern this annotation adds to the output filename."""
        return self._options.get("outputpattern", "-ident")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        """
        return [
            SppasFiles.get_informat_extensions("VIDEO"),
            [".csv"]
            ]
