# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.__init__.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic detection of 68 face landmarks with opencv Facemark.

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

This package requires 'video' feature, for opencv and numpy dependencies.

"""

from sppas.src.config import cfg
from sppas.src.exceptions import sppasEnableFeatureError


if cfg.feature_installed("video") is True:
    # -----------------------------------------------------------------------
    # Import the classes in case the "video" feature is enabled:
    # opencv&numpy are both installed.
    # -----------------------------------------------------------------------
    from .sights import Sights
    from .imgfacemark import ImageFaceLandmark
    from .videosights import sppasSightsVideoBuffer
    from .videosights import sppasSightsVideoWriter
    from .videosights import sppasSightsVideoReader
    from .sppasfacesights import sppasFaceSights

else:
    # -----------------------------------------------------------------------
    # Define exception classes in case opencv&numpy are not installed.
    # -----------------------------------------------------------------------
    class Sights(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class ImageFaceLandmark(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasSightsVideoBuffer(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasSightsVideoWriter(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasSightsVideoReader(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasFaceSights(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


__all__ = (
    "Sights",
    "ImageFaceLandmark",
    "sppasSightsVideoBuffer",
    "sppasSightsVideoWriter",
    "sppasSightsVideoReader",
    "sppasFaceSights"
)
