"""
:filename: sppas.src.config.__init__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Package for the configuration of SPPAS.

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
config: configuration & globals of SPPAS
*****************************************************************************

This package includes classes to fix all global parameters. It does not
requires any other package but all other packages of SPPAS are requiring it!

All classes of this package are compatible with any version of python.

"""

# Utility class to execute and read a subprocess. No external requirement.
from .process import Process

# The global settings. They need to be imported first: others need them.
from .settings import sppasBaseSettings
from .settings import sppasGlobalSettings
from .settings import sppasPathSettings
from .settings import sppasSymbolSettings
from .settings import sppasSeparatorSettings
from .settings import sppasAnnotationsSettings

# Initialize the translation system.
# It requires settings to find .po files.
from .po import sppasTranslate
from .po import error, info, msg

# Utility classes to initialize logs with logging (stream or file).
# It requires settings to print the appropriate headers.
from .logs import sppasLogFile
from .logs import sppasLogSetup

# The trash to put backup files requires the path settings
from .trash import sppasTrash

# SPPAS Application configuration.
# It requires settings for paths, globals...
from .appcfg import sppasAppConfig

# Requires the settings, appcfg and process
from .support import sppasPostInstall

# Requires error, from po
from .exceptions import sppasError               # 0000
from .exceptions import sppasTypeError           # 0100
from .exceptions import sppasIndexError          # 0200
from .exceptions import sppasValueError          # 0300
from .exceptions import sppasKeyError            # 0400
from .exceptions import sppasInstallationError    # 0510
from .exceptions import sppasPermissionError      # 0513
from .exceptions import sppasEnableFeatureError   # 0520
from .exceptions import sppasPackageFeatureError  # 0530
from .exceptions import sppasPackageUpdateFeatureError  # 0540
from .exceptions import sppasIOError             # 0600

from .exceptions import NegativeValueError       # 0310
from .exceptions import RangeBoundsException     # 0320
from .exceptions import IntervalRangeException   # 0330
from .exceptions import IndexRangeException      # 0340

from .exceptions import IOExtensionError         # 0610
from .exceptions import NoDirectoryError         # 0620
from .exceptions import sppasOpenError           # 0650
from .exceptions import sppasWriteError          # 0660
from .exceptions import sppasExtensionReadError  # 0670
from .exceptions import sppasExtensionWriteError  # 0680

# ---------------------------------------------------------------------------
# Fix the global configuration and settings
# ---------------------------------------------------------------------------

# create the global application configuration
cfg = sppasAppConfig()

# create the global log system
lgs = sppasLogSetup(cfg.log_level)
lgs.stream_handler()

# create missing directories
sppasPostInstall().sppas_directories()

# create an instance of each global settings
sg = sppasGlobalSettings()
paths = sppasPathSettings()
symbols = sppasSymbolSettings()
separators = sppasSeparatorSettings()
annots = sppasAnnotationsSettings()

# ---------------------------------------------------------------------------

__all__ = (
    "Process",
    "sppasBaseSettings",
    "sppasGlobalSettings",
    "sppasPathSettings",
    "sppasAnnotationsSettings",
    "sppasSymbolSettings",
    "sppasSeparatorSettings",
    "sppasLogFile",
    "sppasLogSetup",
    "sppasAppConfig",
    "sppasPostInstall",
    "sppasTrash",
    "sg",
    "cfg",
    "lgs",
    "paths",
    "symbols",
    "separators",
    "annots",
    "info",
    "error",
    "msg",
    "sppasError",
    "sppasTypeError",
    "sppasIndexError",
    "sppasValueError",
    "sppasKeyError",
    "sppasInstallationError",
    "sppasPermissionError",
    "sppasEnableFeatureError",
    "sppasPackageFeatureError",
    "sppasPackageUpdateFeatureError",
    "sppasIOError",
    "NegativeValueError",
    "RangeBoundsException",
    "IntervalRangeException",
    "IndexRangeException",
    "IOExtensionError",
    "NoDirectoryError",
    "sppasOpenError",
    "sppasWriteError",
    "sppasExtensionReadError",
    "sppasExtensionWriteError"
)

