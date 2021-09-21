"""
:filename: sppas.__init__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Main package of SPPAS with sources, etc.

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

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Main package of SPPAS: sources, binaries, scripts, translations, etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Import all source packages except those of the UI.

"""

import os
import sys

try:
    from importlib import reload  # Python 3.4+
except ImportError:
    try:
        reload  # Python 2.7
    except NameError:
        from imp import reload  # Python 3.0 - 3.3

# Add this package to the path of Python
sppas_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, sppas_dir)

from sppas.src.config import *
from sppas.src.utils import *
from sppas.src.structs import *
from sppas.src.calculus import *

from sppas.src.wkps import *
from sppas.src.models import *
from sppas.src.resources import *

from sppas.src.anndata import *
from sppas.src.audiodata import *
from sppas.src.imgdata import *
from sppas.src.videodata import *

from sppas.src.annotations import *
from sppas.src.plugins import *

# ---------------------------------------------------------------------------

# Default input/output encoding
reload(sys)
try:
    sys.setdefaultencoding(sg.__encoding__)
except AttributeError:  # Python 2.7
    pass

# sg is an instance of sppasGlobalSettings() defined in config package
__version__ = sg.__version__
__name__ = sg.__name__
__author__ = sg.__author__
__docformat__ = sg.__docformat__
