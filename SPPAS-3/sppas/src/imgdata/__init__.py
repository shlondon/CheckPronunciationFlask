# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.imgdata.__init__.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Package for the management of image files

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

*****************************************************************************
imgdata: management of image files
*****************************************************************************

Requires the following other packages:

* config
* exceptions

Requires the following other external libraries:

* opencv
* numpy

If the video feature is not enabled, the sppasEnableFeatureError() is raised
when a class is instantiated.

"""

import logging

from sppas.src.config import cfg
from sppas.src.config import sppasEnableFeatureError
from sppas.src.config import sppasPackageFeatureError
from sppas.src.config import sppasPackageUpdateFeatureError

# Store the rectangle and a score of an image. No external dependency.
from .coordinates import sppasCoords

# ---------------------------------------------------------------------------


class sppasImageDataError(object):
    def __init__(self, *args, **kwargs):
        raise sppasEnableFeatureError("video")

# ---------------------------------------------------------------------------


try:
    import numpy
    import cv2
    cfg.set_feature("video", True)

except ImportError:
    # Invalidate the feature because the package is not installed
    cfg.set_feature("video", False)

# The feature "video" is enabled: cv2 is installed.
# Check version.
if cfg.feature_installed("video") is True:
    v = cv2.__version__.split(".")[0]
    if v != '4':
        # Invalidate the feature because the package is not up-to-date
        cfg.set_feature("video", False)

    class sppasImageDataError(object):
        def __init__(self, *args, **kwargs):
            if v != '4':
                raise sppasPackageUpdateFeatureError("cv2", "video")
            else:
                raise sppasPackageFeatureError("cv2", "video")


# ---------------------------------------------------------------------------
# Either import classes or define them
# ---------------------------------------------------------------------------

image_extensions = list()

if cfg.feature_installed("video") is True:

    # Subclass of numpy.ndarray to manipulate images
    from .image import sppasImage
    from .imgsequence import ImageSequence
    from .imageutils import sppasImageCompare
    from .imageutils import sppasCoordsCompare
    # Write image and coordinates, read coordinates from csv
    from .imgcoordswriter import sppasCoordsImageWriter
    from .imgcoordswriter import sppasImageCoordsReader
    # Automatically detect objects in an image
    from .objdetec import HaarCascadeDetector
    from .objdetec import NeuralNetONNXDetector
    from .objdetec import NeuralNetTensorFlowDetector
    from .objdetec import NeuralNetCaffeDetector
    from .objdetec import sppasImageObjectDetection
    # Image similarity -- for image clustering or recognition
    from .imgsimilarity import sppasImagesSimilarity

    def opencv_extensions():
        """Return the list of supported file extensions in lower case.

            Windows bitmaps - *.bmp, *.dib (always supported)
            JPEG files - *.jpeg, *.jpg, *.jpe (see the Notes section)
            JPEG 2000 files - *.jp2 (see the Notes section)
            Portable Network Graphics - *.png (see the Notes section)
            Portable image format - *.pbm, *.pgm, *.ppm (always supported)
            Sun rasters - *.sr, *.ras (always supported)
            TIFF files - *.tiff, *.tif (see the Notes section)

        """
        return (".png", ".jpg", ".bmp", ".dib", ".jpeg", ".jpe", ".jp2",
                ".pbm", ".pgm", ".sr", ".ras", ".tiff", ".tif")

    image_extensions.extend(opencv_extensions())

else:
    logging.warning("Support of images is disabled because it requires image feature.")


    class sppasImage(sppasImageDataError):
        pass


    class ImageSequence(sppasImageDataError):
        pass


    class sppasImageCompare(sppasImageDataError):
        pass


    class sppasImagesSimilarity(sppasImageDataError):
        pass


    class sppasCoordsCompare(sppasImageDataError):
        pass


    class sppasCoordsImageWriter(sppasImageDataError):
        pass


    class sppasImageCoordsReader(sppasImageDataError):
        pass


    class HaarCascadeDetector(sppasImageDataError):
        pass


    class NeuralNetONNXDetector(sppasImageDataError):
        pass


    class NeuralNetTensorFlowDetector(sppasImageDataError):
        pass


    class NeuralNetCaffeDetector(sppasImageDataError):
        pass


    class sppasImageObjectDetection(sppasImageDataError):
        pass

# ---------------------------------------------------------------------------


__all__ = (
    "sppasCoords",
    "sppasImage",
    "ImageSequence",
    "sppasImageCompare",
    "sppasImagesSimilarity",
    "sppasCoordsCompare",
    "sppasCoordsImageWriter",
    "sppasImageCoordsReader",
    "image_extensions",
    "HaarCascadeDetector",
    "NeuralNetONNXDetector",
    "NeuralNetTensorFlowDetector",
    "NeuralNetCaffeDetector",
    "sppasImageObjectDetection"
)
