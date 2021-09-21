# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.IVA.intervalvaluesanzlysis.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Eval descriptive stats of values of a tier into intervals

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

from sppas.src.calculus.stats.linregress import tga_linear_regression
from sppas.src.calculus.stats.descriptivesstats import sppasDescriptiveStatistics

# ----------------------------------------------------------------------------


class IntervalValuesAnalysis(sppasDescriptiveStatistics):
    """Interval Values Analysis estimator class.

    This class estimates IVA on a set of data values, stored in a dictionary:

        - key is the name of the segment;
        - value is the list of values observed in each segment.

    >>> d = {'sgmt_1':[1.0, 1.2, 3.2, 4.1] , 'sgmt_2':[2.9, 3.3, 3.6, 5.8]}
    >>> iva = IntervalValuesAnalysis(d)
    >>> mean = iva.mean()
    >>> intercept, slope = iva.intercept_slope()
    >>> print(slope['sgmt_1'])
    >>> print(slope['sgmt_2'])

    """

    def __init__(self, dict_items):
        """Create a new instance of IVA.

        :param dict_items: (dict) a dict of a list of float/int values.

        """
        super(IntervalValuesAnalysis, self).__init__(dict_items)

    # -----------------------------------------------------------------------

    def intercept_slope(self):
        """Estimate the intercept of data values, like for TGA.

        Create the list of points (x,y) of each segment where:
            - x is the item index;
            - y is the value.

        :returns: (dict) a dict of (key, (intercept, slope)) of float values

        """
        lin_reg = list()
        for key, values in self._items.items():
            points = [(pos, val) for pos, val in enumerate(values)]
            lin_reg.append((key, (tga_linear_regression(points))))

        return dict(lin_reg)
