# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.videodata.__init__.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Package for the management of video files.

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
videodata: management of video files
*****************************************************************************

Requires the following other internal packages:

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

# ---------------------------------------------------------------------------


class sppasVideodataError(object):
    def __init__(self, *args, **kwargs):
        raise sppasEnableFeatureError("video")

# ---------------------------------------------------------------------------


try:
    import cv2
    import numpy
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

    class sppasVideoDataError(object):
        def __init__(self, *args, **kwargs):
            if v != '4':
                raise sppasPackageUpdateFeatureError("cv2", "video")
            else:
                raise sppasPackageFeatureError("cv2", "video")


# ---------------------------------------------------------------------------


if cfg.feature_installed("video") is True:
    from .video import sppasVideoReader
    from .video import sppasVideoWriter
    from .videobuffer import sppasVideoReaderBuffer
    from .videocoords import sppasCoordsVideoBuffer
    from .videocoords import sppasCoordsVideoWriter
    from .videocoords import sppasCoordsVideoReader
    from .videoutils import sppasImageVideoWriter
    video_extensions = sppasVideoWriter.get_extensions()

else:
    logging.warning("Support of videos is disabled because it requires video feature.")

    # Define classes in case opencv&numpy are not installed.
    video_extensions = tuple()


    class sppasVideoWriter(sppasVideodataError):
        MAX_FPS = 0
        FOURCC = dict()
        RESOLUTIONS = dict()


    class sppasImageVideoWriter(sppasVideoWriter):
        pass


    class sppasVideoReader(sppasVideodataError):
        pass


    class sppasVideoReaderBuffer(sppasVideodataError):
        DEFAULT_BUFFER_SIZE = 0
        DEFAULT_BUFFER_OVERLAP = 0
        MAX_MEMORY_SIZE = 0
        pass


    class sppasCoordsVideoBuffer(sppasVideodataError):
        pass


    class sppasCoordsVideoWriter(sppasVideoWriter):
        pass


    class sppasCoordsVideoReader(sppasVideoWriter):
        pass


# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------

__all__ = (
    "sppasVideoReader",
    "sppasVideoWriter",
    "sppasImageVideoWriter",
    "sppasVideoReaderBuffer",
    "sppasCoordsVideoBuffer",
    "sppasCoordsVideoWriter",
    "sppasCoordsVideoReader",
    "video_extensions",
)

