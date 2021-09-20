# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceDetection.sppasfacedetect.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  SPPAS integration of the Face detection automatic annotation.

.. _This file is part of SPPAS: <http://www.sppas.org/>
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

import os

from sppas.src.config import cfg
from sppas.src.config import annots
from sppas.src.exceptions import sppasEnableFeatureError

from sppas.src.imgdata import image_extensions
from sppas.src.imgdata import sppasImage
from sppas.src.imgdata import sppasCoordsImageWriter
from sppas.src.videodata import video_extensions
from sppas.src.videodata import sppasCoordsVideoWriter

from ..annotationsexc import AnnotationOptionError
from ..annotationsexc import NoInputError
from ..baseannot import sppasBaseAnnotation

from .imgfacedetect import ImageFaceDetection
from .videofacedetect import VideoFaceDetection

# ---------------------------------------------------------------------------


class sppasFaceDetection(sppasBaseAnnotation):
    """SPPAS integration of the automatic face detection systems.

    Can detect faces in an image or in all images of a video.

    For this annotation, the user can't change the output pattern; it is
    intentional. The pattern is either '-face' or '-portrait' if the option
    portrait is enabled.

    """

    def __init__(self, log=None):
        """Create a new automatic annotation instance.

        :param log: (sppasLog) Human-readable logs.
        :raise: sppasEnableFeatureError

        """
        if cfg.feature_installed("facedetect") is False:
            raise sppasEnableFeatureError("facedetect")

        super(sppasFaceDetection, self).__init__("facedetect.json", log)

        # Face detection in an image
        self.__fdi = ImageFaceDetection()
        self.__img_writer = sppasCoordsImageWriter()

        # Face detection in a video -- actually in all images of a video
        self.__fdv = VideoFaceDetection(self.__fdi)
        self.__video_writer = sppasCoordsVideoWriter(self.__img_writer)

    # -----------------------------------------------------------------------

    def load_resources(self, model1, *args, **kwargs):
        """Fix the model files.

        Currently, both HaarCascade classifiers and DNN are supported. Add
        as many models as wished; their results are combined.

        :param model1: (str) Filename of a model
        :param args: other models for face detection

        """
        self.__fdi.load_model(model1, *args)

    # -----------------------------------------------------------------------
    # Methods to fix options
    # -----------------------------------------------------------------------

    def fix_options(self, options):
        """Fix all options.

        :param options: (sppasOption)

        """
        for opt in options:

            key = opt.get_key()
            if key == "nbest":
                self.set_max_faces(opt.get_value())

            elif key == "score":
                self.set_min_score(opt.get_value())

            elif key == "csv":
                self.set_out_csv(opt.get_value())

            elif key == "tag":
                self.set_img_tag(opt.get_value())

            elif key == "crop":
                self.set_img_crop(opt.get_value())

            elif key == "portrait":
                self.set_img_portrait(opt.get_value())

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

    def set_max_faces(self, value):
        """Fix the maximum number of expected faces in an image.

        :param value: (int) Number of faces

        """
        value = int(value)
        self.__fdv.set_filter_best(value)
        self.__fdi.filter_best(value)
        self._options["nbest"] = value

    # -----------------------------------------------------------------------

    def set_min_score(self, value):
        """Fix the minimum score to accept a face in an image.

        :param value: (float) Min confidence score of face detection result

        """
        value = float(value)
        self.__fdv.set_filter_confidence(value)
        self.__fdi.filter_confidence(value)
        self._options["score"] = value

    # -----------------------------------------------------------------------

    def set_out_csv(self, out_csv=False):
        """The result includes a CSV file.

        :param out_csv: (bool) Create a CSV file when detecting

        """
        self.__video_writer.set_options(csv=out_csv)
        self._options["csv"] = out_csv

    # -----------------------------------------------------------------------

    def set_img_tag(self, value=True):
        """Surround the faces with a square.

        :param value: (bool) Tag the images

        """
        value = bool(value)
        self.__video_writer.set_options(tag=value)
        self._options["tag"] = value

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

    # -----------------------------------------------------------------------

    def set_img_portrait(self, value):
        """Result is the portrait instead of the face.

        :param value: (bool) True

        """
        value = bool(value)
        self._options["portrait"] = value
        self.__fdv.set_portrait(value)

    # -----------------------------------------------------------------------

    def set_out_folder(self, out_folder=False):
        """The result includes a folder with image files -- if video input.

        :param out_folder: (bool) Create a folder with image files when detecting

        """
        self.__video_writer.set_options(folder=out_folder)
        self._options["folder"] = out_folder

    # -----------------------------------------------------------------------
    # Apply the annotation on a given file
    # -----------------------------------------------------------------------

    def image_face_detect(self, image, output=None):
        """Get the image, detect faces and write results.

        :param image: (str) Image filename
        :param output: (str) The output name for the image

        :return: (list) the coordinates of all detected faces or created filenames

        """
        # Get the image from the input
        image = sppasImage(filename=image)

        # Search for coordinates of faces
        self.__fdi.detect(image)

        # Make the output list of coordinates
        if self._options["portrait"] is True:
            try:
                self.__fdi.to_portrait(image)
            except Exception as e:
                self.logfile.print_message(
                    "Faces can't be scaled to portrait: {}".format(str(e)),
                    indent=2, status=annots.error)
        coords = [c.copy() for c in self.__fdi]

        # Save result as a list of coordinates (csv), a tagged image
        # and/or a list of images (face or portrait) in a folder
        if output is not None:
            output_file = self.fix_out_file_ext(output, out_format="IMAGE")
            new_files = self.__img_writer.write(image, coords, output_file, self.get_pattern())
            return new_files

        return coords

    # -----------------------------------------------------------------------

    def run(self, input_file, opt_input_file=None, output=None):
        """Run the automatic annotation process on a single input.

        :param input_file: (list of str) Video or image file
        :param opt_input_file: (list of str) ignored
        :param output: (str) the output name
        :returns: (list of sppasCoords) Coordinates of detected faces or filenames

        """
        # Input is either a video or an image
        fn, ext = os.path.splitext(input_file[0])
        self.__video_writer.set_image_extension(self._out_extensions["IMAGE"])
        self.__video_writer.set_video_extension(self._out_extensions["VIDEO"])
        self.__video_writer.close()

        if ext in image_extensions:
            return self.image_face_detect(input_file[0], output)

        if ext in video_extensions:
            result = self.__fdv.video_face_detect(input_file[0], self.__video_writer, output)
            self.__video_writer.close()
            return result

        self.__video_writer.close()
        raise NoInputError

    # -----------------------------------------------------------------------

    def get_pattern(self):
        """Pattern this annotation uses in an output filename."""
        pattern = "-face"
        if self._options["portrait"] is True:
            pattern = "-portrait"
        return self._options.get("outputpattern", pattern)

    # -----------------------------------------------------------------------

    @staticmethod
    def get_input_extensions():
        """Extensions that the annotation expects for its input filename.

        Priority is given to video files, then image files.

        """
        ext = [e for e in video_extensions]
        ext.extend(image_extensions)
        return ext
