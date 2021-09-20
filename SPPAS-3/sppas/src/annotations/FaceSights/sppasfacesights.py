# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.sppasfacesights.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the automatic annotation FaceSights.

.. _This file is part of SPPAS: http://www.sppas.org/
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

"""

import logging
import os

from sppas.src.config import cfg
from sppas.src.exceptions import sppasEnableFeatureError
from sppas.src.exceptions import sppasError
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import image_extensions
from sppas.src.imgdata import sppasImageCoordsReader
from sppas.src.videodata import video_extensions

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoInputError
from ..baseannot import sppasBaseAnnotation
from ..FaceDetection.imgfacedetect import ImageFaceDetection

from .imgfacemark import ImageFaceLandmark
from .sights import sppasSightsImageWriter
from .videofacemark import VideoFaceLandmark
from .videosights import sppasSightsVideoWriter

# ---------------------------------------------------------------------------

ERR_NO_FACE = "No face detected in the image."

# ---------------------------------------------------------------------------


class sppasFaceSights(sppasBaseAnnotation):
    """SPPAS integration of the automatic face sights annotation.

    """

    def __init__(self, log=None):
        """Create a new sppasFaceSights instance.

        :param log: (sppasLog) Human-readable logs.

        """
        if cfg.feature_installed("facedetect") is False:
            raise sppasEnableFeatureError("facedetect")

        if cfg.feature_installed("facemark") is False:
            raise sppasEnableFeatureError("facemark")

        super(sppasFaceSights, self).__init__("facesights.json", log)
        
        # Face sights detection on an image
        self.__fli = ImageFaceLandmark()
        self.__img_writer = sppasSightsImageWriter()

        # Face sights detection on a video
        self.__flv = VideoFaceLandmark(self.__fli)
        self.__video_writer = sppasSightsVideoWriter(self.__img_writer)

    # -----------------------------------------------------------------------

    def load_resources(self, model_lbf, *args, **kwargs):
        """Fix the model and proto files.

        :param model_lbf: (str) LBF model for landmark
        :param args: other models for landmark (Kazemi/LBF/AAM)

        """
        self.__fli.load_model(model_lbf, *args)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "crop":
                self.set_img_crop(opt.get_value())

            elif key == "folder":
                self.set_out_folder(opt.get_value())

            elif key == "width":
                self.set_img_width(opt.get_value())

            elif key == "height":
                self.set_img_height(opt.get_value())

            elif key in ("inputpattern", "outputpattern", "inputoptpattern"):
                self._options[key] = opt.get_value()

            else:
                raise AnnotationOptionError(key)

    # -----------------------------------------------------------------------
    # Getters and Setters
    # -----------------------------------------------------------------------

    def set_out_csv(self, out_csv=False):
        """The result includes a CSV file.

        :param out_csv: (bool) Create a CSV file with the coordinates

        """
        out_csv = bool(out_csv)
        self.__video_writer.set_options(csv=out_csv)
        self._options["csv"] = out_csv

    # ----------------------------------------------------------------------

    def set_img_tag(self, value=True):
        """Draw the landmark points to the image.

        :param value: (bool) Tag the images

        """
        value = bool(value)
        self.__video_writer.set_options(tag=value)
        self._options["tag"] = value

    # -----------------------------------------------------------------------

    def set_out_folder(self, out_folder=False):
        """The result includes a folder with image files -- if video input.

        :param out_folder: (bool) Create a folder with image files when detecting

        """
        out_folder = bool(out_folder)
        self.__video_writer.set_options(folder=out_folder)
        self._options["folder"] = out_folder

    # -----------------------------------------------------------------------

    def set_img_crop(self, value=True):
        """Create an image/video for each detected person.

        :param value: (bool) Crop the images

        """
        value = bool(value)
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

    # ----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def image_face_sights(self, image_file, csv_faces=None, output=None):
        """Get the image, get or detect faces, eval sights and write results.

        :param image_file: (str) Image filename
        :param output: (str) The output name for the image

        :return: (list) the sights of all detected faces or created filenames

        """
        # Get the image from the input
        image = sppasImage(filename=image_file)

        # Get the coordinates of the face(s) into the image
        coords = None
        if csv_faces is not None:
            if csv_faces.lower().endswith(".csv") is True:
                cr = sppasImageCoordsReader(csv_faces)
                if len(cr.coords) > 0:
                    coords = cr.coords

        if len(coords) == 0:
            raise sppasError(ERR_NO_FACE)

        all_sights = list()
        for face_coord in coords:
            # Search for the sights
            self.__fli.detect_sights(image, face_coord)

            # Get the output list of sights
            sights = self.__fli.get_sights()
            all_sights.append(sights)

        # Save result as a list of sights (csv) and/or a tagged image
        if output is not None:
            output_file = self.fix_out_file_ext(output, out_format="IMAGE")
            new_files = self.__img_writer.write(image, all_sights, output_file, pattern="")
            return new_files

        return all_sights

    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on an input.

        :param input_file: (list of str) Inout file is an image or a video
        :param opt_input_file: (list of str) CSV file with face coordinates
        :param output: (str) the output file name
        :returns: (list of points or filenames) detected sights or created filenames

        """
        # Find the coordinates of the face into the image
        csv_file = None
        if opt_input_file is not None:
            if len(opt_input_file) > 0:
                csv_file = opt_input_file[0]

        # Input is either a video or an image
        fn, ext = os.path.splitext(input_file[0])
        self.__video_writer.set_image_extension(self._out_extensions["IMAGE"])
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])
        self.__video_writer.close()

        if ext in image_extensions:
            return self.image_face_sights(input_file[0], csv_file, output)

        if ext in video_extensions:
            result = self.__flv.video_face_sights(input_file[0], csv_file, self.__video_writer, output)
            self.__video_writer.close()
            return result

        raise NoInputError

    # -----------------------------------------------------------------------

    def get_pattern(self):
        """Pattern this annotation uses in an output filename."""
        return self._options.get("outputpattern", "-sights")

    # -----------------------------------------------------------------------

    def get_opt_input_pattern(self):
        """Pattern that the annotation can optionally use as input."""
        return self._options.get("inputoptpattern", "-ident")

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        Priority is given to video files, then image files.

        """
        ext = [e for e in video_extensions]
        ext.extend(image_extensions)
        return ext