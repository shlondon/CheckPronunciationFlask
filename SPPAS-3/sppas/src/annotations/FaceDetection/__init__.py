# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceDetection.__init__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Automatic detection of faces with opencv.

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

This package requires video feature, for opencv and numpy dependencies.

"""

import logging
from sppas.src.config import cfg
from sppas.src.exceptions import sppasEnableFeatureError

# ---------------------------------------------------------------------------

if cfg.feature_installed("video") is False:
    # Define classes in case opencv&numpy are not installed.
    logging.warning("Face detection is disabled because it requires video feature.")

    class ImageFaceDetection(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class VideoFaceDetection(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasFaceDetection(object):
        def __init__(self, *args, **kwargs):
            raise sppasEnableFeatureError("video")

else:
    # Import the classes in case opencv&numpy are both installed so that
    # the automatic detections can work.

    from .imgfacedetect import ImageFaceDetection
    from .videofacedetect import VideoFaceDetection
    from .sppasfacedetect import sppasFaceDetection

# ---------------------------------------------------------------------------

__all__ = (
    "ImageFaceDetection",
    "VideoFaceDetection",
    "sppasFaceDetection"
)
