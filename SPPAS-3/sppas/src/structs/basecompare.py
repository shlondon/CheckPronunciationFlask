"""
:filename: sppas.src.structs.basecompare.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Base classes to compare data in the filter system.

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

from sppas.src.exceptions import sppasValueError
from sppas.src.exceptions import sppasTypeError
from sppas.src.utils.datatype import sppasType

# ---------------------------------------------------------------------------


class sppasBaseCompare(object):
    """Base class for comparisons.

    """

    def __init__(self):
        """Constructor of a sppasBaseCompare."""
        self.methods = dict()

    # -----------------------------------------------------------------------

    def get(self, name):
        """Return the function of the given name.

        :param name: (str) Simple name of a method of this class

        """
        if name in self.methods:
            return self.methods[name]
        raise sppasValueError(name, "function name")

    # -----------------------------------------------------------------------

    def get_function_names(self):
        """Return the list of comparison functions."""
        return list(self.methods.keys())

# ----------------------------------------------------------------------------


class sppasListCompare(sppasBaseCompare):
    """Comparison methods for two lists.

    """

    def __init__(self):
        """Create a new instance."""
        super(sppasListCompare, self).__init__()

        # Compare the len
        self.methods['leq'] = sppasListCompare.leq
        self.methods['lne'] = sppasListCompare.lne
        self.methods['lgt'] = sppasListCompare.lgt
        self.methods['llt'] = sppasListCompare.llt
        self.methods['lle'] = sppasListCompare.lle
        self.methods['lge'] = sppasListCompare.lge

        # Todo: sppasListCompare for the content of the list

    # -----------------------------------------------------------------------

    @staticmethod
    def leq(elements, x):
        """Return True if number of elements in the list is equal to x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) == x

    # -----------------------------------------------------------------------

    @staticmethod
    def lne(elements, x):
        """Return True if number of elements in the list is not equal to x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) != x

    # -----------------------------------------------------------------------

    @staticmethod
    def lgt(elements, x):
        """Return True if number of elements in the list is greater than x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) > x

    # -----------------------------------------------------------------------

    @staticmethod
    def llt(elements, x):
        """Return True if number of elements in the list is lower than x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) < x

    # -----------------------------------------------------------------------

    @staticmethod
    def lge(elements, x):
        """Return True if number of elements in the list is greater or equal than x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) >= x

    # -----------------------------------------------------------------------

    @staticmethod
    def lle(elements, x):
        """Return True if number of elements in the list is lower or equal than x.

        :param elements: (list)
        :param x: (int)
        :returns: (bool)

        """
        if isinstance(elements, (list, tuple)) is False:
            raise sppasTypeError(elements, "list")
        if sppasType().is_number(x) is False:
            raise sppasTypeError(x, "int/float")

        x = int(x)
        return len(elements) <= x
