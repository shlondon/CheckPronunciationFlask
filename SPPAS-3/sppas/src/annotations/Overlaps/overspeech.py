"""
:filename: sppas.src.annotations.Overlaps.overspeech.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Package for the configuration of SPPAS.

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

from sppas.src.config import error
from sppas.src.exceptions import sppasTypeError
from sppas.src.anndata import sppasTier
from sppas.src.anndata import sppasLocation
from sppas.src.anndata import sppasInterval
from sppas.src.anndata import sppasLabel
from sppas.src.anndata import sppasTag
from ..annotationsexc import EmptyInputError

# ---------------------------------------------------------------------------


class sppasLabelValueError(ValueError):
    """:ERROR 1300:.

    {:s} only supports annotations with one label but the annotation has {:d} labels.

    """

    def __init__(self, data_name, value):
        self._status = 1300
        self.parameter = error(self._status) + \
                         "{:s} only supports annotations with one label but the " \
                         "annotation has {:d} labels.".format(data_name, value)
        # (error(self._status, "annotations")).format(data_name, value)

    def __str__(self):
        return repr(self.parameter)

    def get_status(self):
        return self._status

    status = property(get_status, None)

# ---------------------------------------------------------------------------


class OverActivity(object):
    """Search for overlapped activities.

    """

    def __init__(self, ignore=()):
        """Create a new instance.

        :param ignore: (list of sppasTag) List of tags to ignore.

        """
        self.__outtag = list()
        for tag in ignore:
            if isinstance(tag, sppasTag) is False:
                raise sppasTypeError(tag, "sppasTag")
            self.__outtag.append(tag)

    # -----------------------------------------------------------------------

    def overlaps(self, act1, act2):
        """Return a tier with overlapped activities of given tiers.

        It is supposed that the given tiers have only one label in each
        annotation. Only its best tag is compared.

        :param act1: (sppasTier) Input tier
        :param act2: (sppasTier) Input tier
        :return: (sppasTier)

        """
        # parameters: two interval tiers are expected
        if isinstance(act1, sppasTier) is False:
            raise sppasTypeError(act1, "sppasTier")
        if isinstance(act2, sppasTier) is False:
            raise sppasTypeError(act2, "sppasTier")
        if len(act1) == 0:
            raise EmptyInputError(act1.get_name())
        if len(act2) == 0:
            raise EmptyInputError(act2.get_name())

        if act1.is_interval() is False:
            raise sppasTypeError(act1.get_name(), "Interval Tier")
        if act2.is_interval() is False:
            raise sppasTypeError(act2.get_name(), "Interval Tier")

        tier = sppasTier("Overlapped")
        for ann1 in act1:

            # Ignore the overlap of no labelled annotations
            if ann1.is_labelled() is False:
                continue
            if len(ann1.get_labels()) > 1:
                raise sppasLabelValueError("OverActivity", len(ann1.get_labels()))

            b1 = ann1.get_lowest_localization()
            e1 = ann1.get_highest_localization()
            t1 = ann1.get_best_tag()
            if t1 in self.__outtag:
                continue

            over_anns = act2.find(b1, e1, overlaps=True)
            for ann2 in over_anns:
                if ann2.is_labelled() is False:
                    continue
                if len(ann2.get_labels()) > 1:
                    raise sppasLabelValueError("OverActivity", len(ann2.get_labels()))

                b2 = ann2.get_lowest_localization()
                e2 = ann2.get_highest_localization()
                t2 = ann2.get_best_tag()

                # shared activity
                if t1 == t2:
                    tag = t1.copy()
                    if b2 < b1:
                        if e2 < e1:
                            loc = sppasInterval(b1.copy(), e2.copy())
                        else:
                            loc = sppasInterval(b1.copy(), e1.copy())
                    else:
                        if e2 < e1:
                            loc = sppasInterval(b2.copy(), e2.copy())
                        else:
                            loc = sppasInterval(b2.copy(), e1.copy())

                    tier.create_annotation(sppasLocation(loc), sppasLabel(tag))

        return tier

    # -----------------------------------------------------------------------
    # overloads
    # -----------------------------------------------------------------------

    def __len__(self):
        return len(self.__outtag)

    # -----------------------------------------------------------------------

    def __contains__(self, item):
        return item in self.__outtag

    # ------------------------------------------------------------------------

    def __iter__(self):
        for a in self.__outtag:
            yield a
