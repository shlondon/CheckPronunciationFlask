# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.preinstall.__init__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Package for the management of SPPAS dependencies.

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

Compatible only with Python 3+.

This package allows to:
    - Install external programs with pip, a command manager or a command;
    - Install linguistic resources;
    - Install annotation resources.

"""

from .features import Features
from .installer import Installer
from .depsinstall import sppasInstallerDeps

__all__ = (
    "Features",
    "Installer",
    "sppasInstallerDeps"
)
