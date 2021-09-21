# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.preinstall.depsinstall.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Manage the installer of SPPAS dependencies.

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

import sys
import os
import logging

from .installer import DebianInstaller
from .installer import DnfInstaller
from .installer import RpmInstaller
from .installer import WindowsInstaller
from .installer import MacOsInstaller

# ---------------------------------------------------------------------------


class sppasInstallerDeps(object):
    """Main class to manage the installation of external features.

    sppasInstallerDeps is a wrapper of Installer Object.
    It only allows :
      - to launch the installation process,
      - to get information, which are important for the users,
        about the pre-installation.
      - to configure parameters to get a personalized installation.

    For example:

    >>> installer = sppasInstallerDeps()

    See if a feature is available or not:
    >>> installer.available("feature_id")
    >>> True

    Customize what is enabled or not:
    >>> installer.enable("feature_id")
    >>> False
    >>> installer.enable("feature_id", True)
    >>> True

    Launch the installation process:
    >>> errors = installer.install("feature_id")
    >>> assert len(errors) == 0
    >>> assert installer.available("feature_id") is True

    """

    LIST_OS = {
        "linux": {
            "ubuntu": DebianInstaller,
            "mint": DebianInstaller,
            "debian": DebianInstaller,
            "fedora": DnfInstaller,
            "suse": RpmInstaller,
            "microsoft": DebianInstaller
        },
        "win32": WindowsInstaller,
        "darwin": MacOsInstaller
    }

    def __init__(self, progress=None):
        """Create a new sppasInstallerDeps instance.

        Instantiate the appropriate installer depending on the OS.

        :param progress: (ProcessProgressTerminal) The installation progress.

        """
        self.__os = None
        self.__set_os()
        self.__installer = self.os()()
        logging.info("System installer: {}".format(self.__installer.__class__.__name__))
        if progress is not None:
            self.__installer.set_progress(progress)

        # Update pip before any installation.
        self.__installer.update_pip()

    # ------------------------------------------------------------------------

    def set_progress(self, progress=None):
        self.__installer.set_progress(progress)

    # ------------------------------------------------------------------------

    def features_ids(self, feat_type=None):
        """Return the list of feature identifiers.

        :param feat_type: (str) Only return features of the given type.
        :returns: (list)

        """
        return self.__installer.get_fids(feat_type)

    # ------------------------------------------------------------------------

    def feature_type(self, feat_id):
        """Return the feature type: deps, lang, annot.

        :param feat_id: (str) Identifier of a feature
        :return: (str) or None

        """
        return self.__installer.feature_type(feat_id)

    # ------------------------------------------------------------------------

    def brief(self, feat_id):
        """Return the brief description of the feature.

        :param feat_id: (str) Identifier of a feature

        """
        return self.__installer.brief(feat_id)

    # ------------------------------------------------------------------------

    def description(self, feat_id):
        """Return the description of the feature.

        :param feat_id: (str) Identifier of a feature

        """
        return self.__installer.description(feat_id)

    # ------------------------------------------------------------------------

    def available(self, feat_id):
        """Return True if the feature is available.

        :param feat_id: (str) Identifier of a feature

        """
        return self.__installer.available(feat_id)

    # ------------------------------------------------------------------------

    def os(self):
        """Return the OS of the computer."""
        return self.__os

    # ------------------------------------------------------------------------

    def __set_os(self):
        """Set the OS of the computer."""
        system = sys.platform
        logging.info("Operating system: {}".format(system))
        if system.startswith("linux") is True:
            distrib = str(os.uname()).split(", ")[3].split("-")[1].split(" ")[0].lower()
            logging.info("Distrib: {}".format(distrib))
            if distrib in sppasInstallerDeps.LIST_OS["linux"]:
                self.__os = sppasInstallerDeps.LIST_OS["linux"][distrib]
            else:
                raise OSError("The distrib {:s} for system {:s} is not supported yet.".format(distrib, system))

        else:
            if system not in list(sppasInstallerDeps.LIST_OS.keys()):
                raise OSError("The OS {} is not supported yet.".format(system))
            else:
                self.__os = sppasInstallerDeps.LIST_OS[system]

    # ------------------------------------------------------------------------

    def enable(self, fid, value=None):
        """Return True if the feature is enabled and/or set it.

        :param fid: (str) Identifier of a feature
        :param value: (bool or None) Enable of disable the feature.

        """
        if value is None:
            return self.__installer.enable(fid)

        return self.__installer.enable(fid, value)

    # ------------------------------------------------------------------------

    def install(self, feat_type=None):
        """Launch the installation process.

        :return errors: (str) errors happening during installation.

        """
        errors = self.__installer.install(feat_type)
        return errors

