# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.__init__.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Set a person identity to detected faces of a video.

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

This package requires video feature, for opencv and numpy dependencies.

"""

import logging

from sppas.src.config import cfg
from sppas.src.exceptions import sppasEnableFeatureError

# ---------------------------------------------------------------------------

if cfg.feature_installed("video") is False:
    # Define exception classes in case opencv&numpy are not installed.
    logging.warning("Face identification is disabled because it requires video feature.")

    class VideoPersonIdentity(object):
        def __init__(self):
            raise sppasEnableFeatureError("video")


    class sppasFaceIdentifier(object):
        def __init__(self, *args, **kwargs):
            raise sppasEnableFeatureError("video")

else:
    # Import the classes in case the "video" feature is enabled,
    # opencv&numpy are both installed and the automatic can work.

    from .identifycoords import VideoCoordsIdentification
    from .sppasfaceid import sppasFaceIdentifier

# ---------------------------------------------------------------------------

__all__ = (
    "VideoCoordsIdentification",
    "sppasFaceIdentifier"
)
