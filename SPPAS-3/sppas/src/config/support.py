# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.config.support.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Support of SPPAS. Currently under development.

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

import os
import shutil
import logging

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from .settings import sppasPathSettings
from .settings import sppasGlobalSettings

# ---------------------------------------------------------------------------


class sppasPostInstall:
    """Check directories and create if not existing.

    """

    @staticmethod
    def sppas_directories():
        """Create the required directories in the SPPAS package.

        :raise: sppasPermissionError

        """
        logging.info("Check directories and create if not existing:")

        with sppasPathSettings() as paths:

            # Test if we have the rights to write into the SPPAS directory
            sppas_parent_dir = os.path.dirname(paths.basedir)
            try:
                os.mkdir(os.path.join(sppas_parent_dir, "sppas_test"))
                shutil.rmtree(os.path.join(sppas_parent_dir, "sppas_test"))
                logging.info(" - Write access to SPPAS package directory is granted.")
            except OSError as e:
                # Check for write access
                logging.critical("Write access denied to {:s}. SPPAS package should be "
                                 "installed elsewhere.".format(sppas_parent_dir))
                logging.error(str(e))

            if os.path.exists(paths.logs) is False:
                os.mkdir(paths.logs)
                logging.info(" - The directory {:s} to store logs is created.".format(paths.logs))
            else:
                logging.info(" - The folder for logs is OK.")

            if os.path.exists(paths.wkps) is False:
                os.mkdir(paths.wkps)
                logging.info("The directory {:s} to store workspaces is created.".format(paths.wkps))
            else:
                logging.info(" - The folder for the workspaces is OK.")

            if os.path.exists(paths.trash) is False:
                os.mkdir(paths.trash)
                logging.info("The Trash directory {:s} is created.".format(paths.trash))
            else:
                logging.info(" - The trash is OK.")

    # -----------------------------------------------------------------------

    @staticmethod
    def sppas_dependencies():
        """Enable or disable features depending on dependencies."""
        pass


# ---------------------------------------------------------------------------


class sppasUpdate:
    """Check if an update of SPPAS is available.

    This class is not implemented yet.

    """

    @staticmethod
    def check_update():
        with sppasGlobalSettings as sg:
            current = sg.__version__

            # Perhaps I should create a text file with the version number
            url = sg.__url__ + '/download.html'
            response = urlopen(url)
            data = str(response.read())

            # Extract last version from this page

            # Compare to current version

        return False
