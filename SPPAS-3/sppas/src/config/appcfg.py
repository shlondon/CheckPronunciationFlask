#!/usr/bin/env python
# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.config.appcfg.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  The application configuration.

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
import sys
import json

from .settings import sppasPathSettings

# ---------------------------------------------------------------------------


class sppasAppConfig(object):
    """Configuration for SPPAS application.

    An instance of this class has to be created for any application using
    the SPPAS API.

    Members are:

        - log_level
        - splash_delay
        - features dictionary

    """

    APP_CONFIG_FILENAME = ".app~"
    DEFAULT_LOG_LEVEL = 0
    DEFAULT_SPLASH_DELAY = 3

    # -----------------------------------------------------------------------

    def __init__(self):
        """Create a new sppasAppConfig instance.

        The configuration is set to its default values and updated
        with the content of a configuration file (if existing).

        The configuration is saved the 1st time this class is instantiated
        and when this class is deleted.

        """
        super(sppasAppConfig, self).__init__()

        # Create a default configuration
        self.__log_level = sppasAppConfig.DEFAULT_LOG_LEVEL
        self.__splash_delay = sppasAppConfig.DEFAULT_SPLASH_DELAY
        self.__feat_ids = dict()

        # Load the existing configuration file (if any)
        self.load()

    # -----------------------------------------------------------------------

    def __enter__(self):
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        # self.save()
        pass

    # -----------------------------------------------------------------------

    def get_log_level(self):
        """Return the level for logging messages, ranging 0-50."""
        return self.__log_level

    def set_log_level(self, value):
        """Set the log level for the application.

        :param value: (int) Logging ranges from 0 (any) to 50 (critical only).

        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 50:
            value = 50
        self.__log_level = value

    log_level = property(get_log_level, set_log_level)

    # -----------------------------------------------------------------------

    def get_splash_delay(self):
        """Return the delay the splash will be displayed (in seconds)."""
        return self.__splash_delay

    def set_splash_delay(self, value):
        """Set the delay to draw the splash.

        :param value: (int) Delay ranging 0..10 seconds.

        """
        value = int(value)
        if value < 0:
            value = 0
        if value > 10:
            value = 10
        self.__splash_delay = value

    splash_delay = property(get_splash_delay, set_splash_delay)

    # -----------------------------------------------------------------------

    @staticmethod
    def cfg_filename():
        """Return the name of the config file."""
        with sppasPathSettings() as paths:
            cfg_filename = os.path.join(paths.basedir, sppasAppConfig.APP_CONFIG_FILENAME)
        return cfg_filename

    # ------------------------------------------------------------------------

    def load(self):
        """Load the configuration from a file."""
        cfg = self.cfg_filename()

        if os.path.exists(cfg) is False:
            # The file isn't existing. It's the first launch. Save it
            # with the default values.
            self.save()

        else:
            with open(self.cfg_filename()) as cfg:
                d = json.load(cfg)

                self.__splash_delay = d.get("splash_delay", sppasAppConfig.DEFAULT_SPLASH_DELAY)
                self.__log_level = d.get("log_level", sppasAppConfig.DEFAULT_LOG_LEVEL)

                # Load the deps of the file without deleting the ones already in
                # the dict: add or override the deps of the file to our dict.
                deps = d.get("features", dict())
                for key in deps:
                    self.__feat_ids[key] = deps[key]

    # ------------------------------------------------------------------------

    def save(self):
        """Save into a JSON file."""
        # Admin rights are needed to write in an hidden file. So it's needed
        # to switch the file in a normal mode in order to modify it and then
        # to hide back the file.
        self.__hide(False)
        with open(self.cfg_filename(), "w") as f:
            d = dict()
            d["log_level"] = self.__log_level
            d["splash_delay"] = self.__splash_delay
            d["features"] = self.__feat_ids
            f.write(json.dumps(d, indent=2))

        self.__hide(True)

    # ------------------------------------------------------------------------

    def __hide(self, value):
        """Hide or un-hide a file.

        :param value: (bool) Hide the config filename

        """
        filename = self.cfg_filename()
        system = sys.platform
        if system == "win32":
            oper = "+"
            if value is False:
                oper = "-"
            p = os.popen('attrib ' + oper + 'h ' + filename)
            p.close()

    # ------------------------------------------------------------------------
    # Methods related to the list of available features.
    # ------------------------------------------------------------------------

    def get_feature_ids(self):
        """Return the list of feature identifiers currently known."""
        return list(self.__feat_ids.keys())

    # ------------------------------------------------------------------------

    def feature_installed(self, key):
        """Return True if a feature was successfully installed by SPPAS.

        :param key: (str) Identifier of a feature.

        """
        if key not in self.__feat_ids:
            return False
        return self.__feat_ids[key]

    # ------------------------------------------------------------------------

    def set_feature(self, key, value):
        """Add or update a feature.

        This change is set to the current dict but is not saved in the
        configuration file.

        :param key: (str) Identifier of a feature
        :param value: (bool) Installed or disabled

        """
        self.__feat_ids[key] = bool(value)

