# -*- coding: UTF-8 -*-
"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech

        http://www.sppas.org/

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

        ---------------------------------------------------------------------

    anndata.tier.py
    ~~~~~~~~~~~~~~~~

"""

import logging

from sppas.src.utils import sppasUnicode

from .anndataexc import AnnDataTypeError
from .anndataexc import AnnDataIndexError
from .anndataexc import IntervalBoundsError
from .anndataexc import CtrlVocabContainsError
from .anndataexc import TierAppendError
from .anndataexc import TierAddError
from .anndataexc import TrsAddError

from .ann.annlocation import sppasPoint
from .ann.annotation import sppasAnnotation
from .ann.annlocation import sppasInterval
from .ann.annlocation import sppasLocation
from .metadata import sppasMetaData
from .ctrlvocab import sppasCtrlVocab
from .media import sppasMedia

# ----------------------------------------------------------------------------


class sppasTier(sppasMetaData):
    """Representation of a tier, a structured set of annotations.

    Annotations of a tier are sorted depending on their location
    (from lowest to highest).

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2017  Brigitte Bigi

    A Tier is made of:

        - a name (used to identify the tier),
        - a set of metadata,
        - an array of annotations,
        - a controlled vocabulary (optional),
        - a media (optional),
        - a parent (optional).

    """

    def __init__(self, name=None, ctrl_vocab=None, media=None, parent=None):
        """Create a new sppasTier instance.

        :param name: (str) Name of the tier. It is used as identifier.
        :param ctrl_vocab: (sppasCtrlVocab)
        :param media: (sppasMedia)
        :param parent: (sppasTranscription)

        """
        super(sppasTier, self).__init__()

        self.__name = None
        self.__ann = list()
        self.__ctrl_vocab = None
        self.__media = None
        self.__parent = None

        self.set_name(name)
        self.set_ctrl_vocab(ctrl_vocab)
        self.set_media(media)
        self.set_parent(parent)

    # -----------------------------------------------------------------------
    # Getters
    # -----------------------------------------------------------------------

    def get_name(self):
        """Return the identifier name of the tier."""
        return self.__name

    # -----------------------------------------------------------------------

    def get_ctrl_vocab(self):
        """Return the controlled vocabulary of the tier."""
        return self.__ctrl_vocab

    # -----------------------------------------------------------------------

    def get_media(self):
        """Return the media of the tier."""
        return self.__media

    # -----------------------------------------------------------------------

    def get_parent(self):
        """Return the parent of the tier."""
        return self.__parent

    # -----------------------------------------------------------------------
    # Setters
    # -----------------------------------------------------------------------

    def set_name(self, name=None):
        """Set the name of the tier.

        If no name is given, an GUID is randomly assigned.
        Important: An empty string is accepted.

        :param name: (str) The identifier name or None.
        :returns: the formatted name

        """
        if name is None:
            if self.get_id() == "":
                self.gen_id()
            name = self.get_id()
        su = sppasUnicode(name)
        self.__name = su.to_strip()

        return self.__name

    # -----------------------------------------------------------------------

    def set_ctrl_vocab(self, ctrl_vocab=None):
        """Set a controlled vocabulary to this tier.

        :param ctrl_vocab: (sppasCtrlVocab or None)
        :raises: AnnDataTypeError, CtrlVocabContainsError

        """
        if ctrl_vocab is not None:
            if isinstance(ctrl_vocab, sppasCtrlVocab) is False:
                raise AnnDataTypeError(ctrl_vocab, "sppasCtrlVocab")

            # Check all annotation tags to validate the
            # ctrl_vocab before assignment
            for annotation in self.__ann:
                for label in annotation.get_labels():
                    annotation.validate_label(label)

            if self.__parent is not None:
                try:
                    self.__parent.add_ctrl_vocab(ctrl_vocab)
                except TrsAddError:
                    pass

        self.__ctrl_vocab = ctrl_vocab

    # -----------------------------------------------------------------------

    def set_media(self, media):
        """Set a media to the tier.

        :param media: (sppasMedia)
        :raises: AnnDataTypeError

        """
        if media is not None:
            if isinstance(media, sppasMedia) is False:
                raise AnnDataTypeError(media, "sppasMedia")
            if self.__parent is not None:
                try:
                    self.__parent.add_media(media)
                except TrsAddError:
                    pass

        self.__media = media

    # -----------------------------------------------------------------------

    def set_parent(self, parent):
        """Set the parent of the tier.

        :param parent: (sppasTranscription)

        """
        self.__parent = parent

        if parent is not None:
            # add the media to the parent
            if self.__media is not None:
                try:
                    self.__parent.add_media(self.__media)
                except TrsAddError:
                    pass

            # add the controlled vocabulary to the parent
            if self.__ctrl_vocab is not None:
                try:
                    self.__parent.add_ctrl_vocab(self.__ctrl_vocab)
                except TrsAddError:
                    pass

    # -----------------------------------------------------------------------

    def copy(self):
        """Return a deep copy of the tier.

        :return: (sppasTier) including the 'id'.

        """
        new_tier = sppasTier(self.__name)
        my_parent = self.get_parent()
        self.set_parent(None)
        new_tier.set_parent(None)
        new_tier.set_ctrl_vocab(self.__ctrl_vocab)  # set a copy ???
        new_tier.set_media(self.__media)            # set a copy ???
        for a in self.__ann:
            new_ann = a.copy()
            new_tier.add(new_ann)
        # metadata
        for key in self.get_meta_keys():
            new_tier.set_meta(key, self.get_meta(key))

        new_tier.set_parent(my_parent)
        self.__parent = my_parent
        return new_tier

    # -----------------------------------------------------------------------
    # Annotations
    # -----------------------------------------------------------------------

    def create_annotation(self, location, labels=None):
        """Create and add a new annotation into the tier.

        :param location: (sppasLocation) the location(s) where \
               the annotation happens
        :param labels: (sppasLabel, list) the label(s) to stamp this annot.
        :returns: sppasAnnotation

        """
        ann = sppasAnnotation(location, labels)
        self.add(ann)
        return ann

    # -----------------------------------------------------------------------

    def create_annotation_before(self, idx):
        """Create and add a new annotation in the hole before idx.

        :param idx: (int) Index of an existing annotation
        :returns: sppasAnnotation
        :raises AnnDataTypeError, AnnDataIndexError

        """
        if self.is_point():
            raise AnnDataTypeError(self.get_name(), "Interval, Disjoint")

        try:
            ann = self.__ann[idx]
        except IndexError:
            raise AnnDataIndexError(idx)

        if idx == 0:
            if self.is_int():
                begin = sppasPoint(0)
            else:
                begin = sppasPoint(0.)
        else:
            prev_ann = self.__ann[idx-1]
            begin = prev_ann.get_highest_localization()
        end = ann.get_lowest_localization()

        new_ann = self.create_annotation(sppasLocation(sppasInterval(begin, end)))
        return new_ann

    # -----------------------------------------------------------------------

    def create_annotation_after(self, idx):
        """Create and add a new annotation in the hole after idx.

        :param idx: (int) Index of an existing annotation
        :returns: sppasAnnotation
        :raises AnnDataTypeError, AnnDataIndexError

        """
        if self.is_point():
            raise AnnDataTypeError(self.get_name(), "Interval, Disjoint")
        if idx+1 == len(self.__ann):
            raise AnnDataIndexError(idx+1)
        try:
            ann = self.__ann[idx]
            next_ann = self.__ann[idx+1]
        except IndexError:
            raise AnnDataIndexError(idx)

        begin = ann.get_highest_localization()
        end = next_ann.get_lowest_localization()

        new_ann = self.create_annotation(sppasLocation(sppasInterval(begin, end)))
        return new_ann

    # -----------------------------------------------------------------------

    def is_empty(self):
        """Return True if the tier does not contain annotations."""
        return len(self.__ann) == 0

    # -----------------------------------------------------------------------

    def append(self, annotation):
        """Append the given annotation at the end of the tier.

        Assign this tier as parent to the annotation.

        :param annotation: (sppasAnnotation)
        :raises: AnnDataTypeError, CtrlVocabContainsError, \
        HierarchyContainsError, HierarchyTypeError, TierAppendError

        """
        self.validate_annotation(annotation)

        if len(self.__ann) > 0:
            end = self.__ann[-1].get_highest_localization()
            new = annotation.get_lowest_localization()
            if annotation.location_is_point() and end == new:
                raise TierAppendError(end, new)
            if end > new:
                raise TierAppendError(end, new)

        self.__ann.append(annotation)

    # -----------------------------------------------------------------------

    def add(self, annotation):
        """Add an annotation to the tier in sorted order.

        Assign this tier as parent to the annotation.

        :param annotation: (sppasAnnotation)
        :raises: AnnDataTypeError, CtrlVocabContainsError, \
        HierarchyContainsError, HierarchyTypeError
        :returns: the index of the annotation in the tier

        """
        self.validate_annotation(annotation)
        try:
            self.append(annotation)
        except Exception:

            if annotation.location_is_point():
                index = self.index(annotation.get_lowest_localization())
                if index != -1:
                    if self.__ann[index].get_lowest_localization().get_midpoint() == \
                            annotation.get_lowest_localization().get_midpoint():
                        raise TierAddError(index)
                    self.__ann.insert(index + 1, annotation)
                    return index + 1
                else:
                    index = self.near(annotation.get_lowest_localization(), direction=-1)
                    self.__ann.insert(index, annotation)
                    return index

            else:
                index = self.mindex(annotation.get_lowest_localization(), bound=0)

                # We go further to look at the next localizations until the begin is smaller.
                while index + 1 < len(self.__ann) and \
                        self.__ann[index + 1].get_lowest_localization() < annotation.get_lowest_localization():
                    index += 1
                # We go further to look at the next localizations until the end is smaller.
                while index + 1 < len(self.__ann) and \
                        self.__ann[index + 1].get_lowest_localization() == annotation.get_lowest_localization() and \
                        self.__ann[index + 1].get_highest_localization() < annotation.get_highest_localization():
                    index += 1

                if self.__ann[index].get_location() == annotation.get_location():
                    raise TierAddError(index)

                if index+1 < len(self.__ann):
                    if self.__ann[index+1].get_location() == annotation.get_location():
                        raise TierAddError(index+1)

                self.__ann.insert(index + 1, annotation)
                return index + 1

        return len(self.__ann) - 1

    # -----------------------------------------------------------------------

    def remove(self, begin, end, overlaps=False):
        """Remove annotation intervals between begin and end.

        :param begin: (sppasPoint)
        :param end: (sppasPoint)
        :param overlaps: (bool)
        :returns: the number of removed annotations
        :raises: HierarchyContainsError

        """
        if end < begin:
            raise IntervalBoundsError(begin, end)

        annotations = self.find(begin, end, overlaps)

        copied_anns = list()
        for a in reversed(annotations):
            copied_anns.append(a.copy())
            self.__ann.remove(a)

        if self.__parent is not None:
            try:
                self.validate()
            except:
                for a in copied_anns:
                    self.add(a)

        return len(copied_anns)

    # -----------------------------------------------------------------------

    def pop(self, index=-1):
        """Remove the annotation at the given position in the tier.

        If no index is specified, pop() removes
        and returns the last annotation in the tier.

        :param index: (int) Index of the annotation to remove.
        :raises: HierarchyContainsError

        """
        try:
            ann = self.__ann[index]
            copied_ann = ann.copy()
        except IndexError:
            raise AnnDataIndexError(index)

        self.__ann.pop(index)
        if self.__parent is not None:
            try:
                self.validate()
            except:
                self.__ann.insert(index, copied_ann)
                raise

    # -----------------------------------------------------------------------

    def remove_unlabelled(self):
        """Remove annotations without labels.

        Do not remove an annotation if it invalidates the hierarchy.

        :returns: the number of removed annotations

        """
        nb = 0
        for a in reversed(self.__ann):
            if a.is_labelled() is False:
                try:
                    self.__ann.remove(a)
                    nb += 1
                except:
                    # we should write a message to logging
                    pass
        return nb

    # -----------------------------------------------------------------------

    def split(self, idx):
        """Split annotation at the given index into 2 annotations.

        :param idx: (int) Index of the annotation to split.
        :return: newly created annotation at index idx+1

        """
        if self.is_point() is True:
            raise AnnDataTypeError(self.get_name(), "Interval, Disjoint")

        try:
            ann = self.__ann[idx]
        except IndexError:
            raise AnnDataIndexError(idx)

        localization = ann.get_location().get_best()
        end = localization.get_end().copy()
        middle = localization.middle()

        try:
            localization.set_end(middle)
            self.validate()
            new_ann = self.create_annotation(
                sppasLocation(sppasInterval(middle.copy(), end)))
        except:
            localization.set_end(end)
            raise

        return new_ann

    # -----------------------------------------------------------------------

    def merge(self, idx, direction):
        """Merge the annotation at given index with next or previous one.

        if direction > 0:
            ann_idx:  [begin_idx, end_idx, labels_idx]
            next_ann: [begin_n, end_n, labels_n]
            result:   [begin_idx, end_n, labels_idx + labels_n]

        if direction < 0:
            prev_ann: [begin_p, end_p, labels_p]
            ann_idx:  [begin_idx, end_idx, labels_idx]
            result:   [begin_p, end_idx, labels_p + labels_idx]

        :param idx: (int) Index of the annotation in the list
        :param direction: (int) Positive for next, Negative for previous
        :return: (bool) False if direction does not match with index
        :raise: Exception if merged annotation can't be deleted of the tier

        """
        if self.is_point() is True:
            raise AnnDataTypeError(self.get_name(), "Interval, Disjoint")

        try:
            ann = self.__ann[idx]
        except IndexError:
            raise AnnDataIndexError(idx)

        # Get the next or previous annotation
        if direction > 0:
            merge_idx = idx + 1
            if merge_idx == len(self.__ann):
                return False
        else:
            if idx == 0:
                return False
            merge_idx = idx - 1
        merge_ann = self.__ann[merge_idx]

        merge_labels = [l.copy() for l in merge_ann.get_labels()]
        merge_loc = merge_ann.get_location().get_best()

        # Create a copy of its labels and its localization
        localization = ann.get_location().get_best()
        copied_loc = localization.copy()
        labels = self.__ann[idx].get_labels()

        try:
            # Modify the localization at idx
            if direction > 0:
                localization.set_end(merge_loc.get_end())
                new_labels = labels + merge_labels
            else:
                localization.set_begin(merge_loc.get_begin())
                new_labels = merge_labels + labels
            # will raise an exception is modifs imply to brake hierarchy
            self.validate()

            # Update labels and delete next/previous ann
            ann.set_labels(new_labels)
            self.pop(merge_idx)
        except:
            # Restore modified ann
            ann.set_best_localization(copied_loc)
            ann.set_labels(labels)
            raise

        return True

    # -----------------------------------------------------------------------
    # Localizations
    # -----------------------------------------------------------------------

    def get_all_points(self):
        """Return the list of all points of the tier."""
        if len(self.__ann) == 0:
            return []

        points = list()
        for ann in self.__ann:
            points.extend(ann.get_all_points())

        return points

    # -----------------------------------------------------------------------

    def get_first_point(self):
        """Return the first point of the first annotation."""
        if len(self.__ann) == 0:
            return None

        return self.__ann[0].get_lowest_localization()

    # -----------------------------------------------------------------------

    def get_last_point(self):
        """Return the last point of the last location."""
        if len(self.__ann) == 0:
            return None

        return self.__ann[-1].get_highest_localization()

    # -----------------------------------------------------------------------

    def has_point(self, point):
        """Return True if the tier contains a given point.

        :param point: (sppasPoint) The point to find in the tier.
        :returns: (bool)

        """
        if isinstance(point, sppasPoint) is False:
            raise AnnDataTypeError(point, "sppasPoint")

        return point in self.get_all_points()

    # -----------------------------------------------------------------------

    def has_location(self, location):
        """Return True if the tier has the given location.

        to be tested.

        """
        # Use 'find' for a faster search
        begin = location.get_lowest_localization()
        end = location.get_highest_localization()
        anns = self.find(begin, end, overlaps=False)
        for a in anns:
            if a.get_location() == location:
                return True
        return False

    # -----------------------------------------------------------------------

    def is_disjoint(self):
        """Return True if the tier is made of disjoint localizations."""
        if len(self.__ann) == 0:
            return False

        return self.__ann[0].get_location().is_disjoint()

    # -----------------------------------------------------------------------

    def is_interval(self):
        """Return True if the tier is made of interval localizations."""
        if len(self.__ann) == 0:
            return False

        return self.__ann[0].get_location().is_interval()

    # -----------------------------------------------------------------------

    def is_point(self):
        """Return True if the tier is made of point localizations."""
        if len(self.__ann) == 0:
            return False

        return self.__ann[0].get_location().is_point()

    # -----------------------------------------------------------------------

    def get_midpoint_intervals(self):
        """Return midpoint values of all the intervals."""
        units = list()
        if self.is_point() is False:
            for i in range(len(self)):
                b = self.__ann[i].get_lowest_localization().get_midpoint()
                e = self.__ann[i].get_highest_localization().get_midpoint()
                units.append((b, e))

        return units

    # -----------------------------------------------------------------------

    def get_midpoint_points(self):
        """Return midpoint values of all the points."""
        units = list()
        if self.is_point() is True:
            for i in range(len(self)):
                m = self.__ann[i].get_lowest_localization().get_midpoint()
                units.append(m)

        return units

    # -----------------------------------------------------------------------

    def set_radius(self, radius):
        """Fix a radius value to all points of the tier.

        :param radius: (int, float) New radius value
        :raise: AnnDataTypeError, AnnDataNegValueError

        """
        for ann in self.__ann:
            ann.get_location().set_radius(radius)

    # -----------------------------------------------------------------------

    def find(self, begin, end, overlaps=True, indexes=False):
        """Return a list of annotations between begin and end.

        :param begin: sppasPoint or None to start from the beginning of the tier
        :param end: sppasPoint or None to end at the end of the tier
        :param overlaps: (bool) Return also overlapped annotations. \
                  Not relevant for tiers with points.
        :param indexes: (bool) Return indexes instead of annotations
        :returns: List of sppasAnnotation or list of indexes

        """
        if len(self.__ann) == 0:
            return []

        if begin is None:
            begin = self.get_first_point()

        if end is None:
            end = self.get_last_point()

        # Out of interval!
        if begin > self.get_last_point() or end < self.get_first_point():
            return []

        annotations = list()

        if self.is_point() is True:

            lo = self.index(begin)
            if lo == -1:
                lo = self.near(begin, direction=1)
            for i, ann in enumerate(self.__ann[lo:]):
                lowest = ann.get_lowest_localization()
                highest = ann.get_highest_localization()
                if lowest > end and highest > end:
                    break
                if lowest >= begin and highest <= end:
                    if indexes is True:
                        annotations.append(lo+i)
                    else:
                        annotations.append(ann)

        else:
            lo = self.__find(begin)

            if overlaps is True:
                if lo > 0:
                    tmp_annotations = list()
                    for ann in reversed(self.__ann[:lo]):
                        b = ann.get_lowest_localization()
                        e = ann.get_highest_localization()
                        if b < begin < e:
                            tmp_annotations.append(ann)
                        if b > begin:
                            break
                    for i, ann in enumerate(reversed(tmp_annotations)):
                        if indexes is True:
                            annotations.append(lo + i)
                        else:
                            annotations.append(ann)
                else:
                    annotations = list()
                for i, ann in enumerate(self.__ann[lo:]):
                    b = ann.get_lowest_localization()
                    e = ann.get_highest_localization()
                    if b >= end:
                        break
                    if end > b and begin < e:
                        if indexes is True:
                            annotations.append(lo + i)
                        else:
                            annotations.append(ann)
            else:
                annotations = list()
                for i, ann in enumerate(self.__ann[lo:]):
                    b = ann.get_lowest_localization()
                    e = ann.get_highest_localization()
                    if b >= begin and e <= end:
                        if indexes is True:
                            annotations.append(lo + i)
                        else:
                            annotations.append(ann)
                    if b >= end:
                        break

        return annotations

    # -----------------------------------------------------------------------

    def index(self, moment):
        """Return the index of the moment (int), or -1.

        Only for tier with points.

        :param moment: (sppasPoint)

        """
        if self.is_point() is False:
            return -1

        lo = 0
        hi = len(self.__ann)
        mid = (lo + hi) // 2
        found = False
        while lo < hi:
            mid = (lo + hi) // 2
            a = self.__ann[mid]
            if moment < a.get_lowest_localization():
                hi = mid
            elif moment > a.get_lowest_localization():
                lo = mid + 1
            else:
                found = True
                break

        if found is False:
            return -1

        return mid

    # ------------------------------------------------------------------------

    def lindex(self, moment):
        """Return the index of the interval starting at a given moment, or -1.

        Only for tier with intervals or disjoint.
        If the tier contains more than one annotation starting at the same
        moment, the method returns the first one.

        :param moment: (sppasPoint)

        """
        if self.is_point() is True:
            return -1

        lo = 0
        hi = len(self.__ann)
        mid = (lo + hi) // 2
        found = False
        while lo < hi:
            mid = (lo + hi) // 2
            begin = self.__ann[mid].get_lowest_localization()
            if moment < begin:
                hi = mid
            elif moment > begin:
                lo = mid + 1
            else:
                found = True
                break
        if found is False:
            return -1
        if mid == 0:
            return 0

        # We go back to look at the previous localizations
        # until they are different.
        while mid >= 0 and self.__ann[mid].get_lowest_localization() == moment:
            mid -= 1

        return mid + 1

    # ------------------------------------------------------------------------

    def mindex(self, moment, bound=0):
        """Return index of the interval containing the given moment.

        Only for tier with intervals or disjoint.

        If the tier contains more than one annotation at the same moment,
        the method returns the first one (i.e. the one which started at first).

        :param moment: (sppasPoint)
        :param bound: (int)
            - 0 to exclude bounds of the interval;
            - -1 to include begin bound;
            - +1 to include end bound;
            - +2 to include both begin/end bounds;
            - others: the midpoint of moment is strictly inside
        :returns: (int) Index of the 1st annotation containing moment or -1

        """
        if self.is_point() is True:
            return -1

        for i, a in enumerate(self.__ann):
            b = a.get_lowest_localization()
            e = a.get_highest_localization()
            if bound == -1:
                if b <= moment < e:
                    return i
            elif bound == 1:
                if b < moment <= e:
                    return i
            elif bound == 2:
                if b <= moment <= e:
                    return i
            elif bound == 0:
                if b < moment < e:
                    return i
            else:
                if b < moment.get_midpoint() < e:
                    return i

        return -1

    # ------------------------------------------------------------------------

    def rindex(self, moment):
        """Return the index of the interval ending at the given moment.

        Only for tier with intervals or disjoint.
        If the tier contains more than one annotation ending at the same moment,
        the method returns the last one.

        :param moment: (sppasPoint)

        """
        if self.is_point() is True:
            return -1

        lo = 0
        hi = len(self.__ann)
        mid = (lo + hi) // 2
        found = False
        while lo < hi:
            mid = (lo + hi) // 2
            a = self.__ann[mid]
            if moment < a.get_highest_localization():
                hi = mid
            elif moment > a.get_highest_localization():
                lo = mid + 1
            else:
                found = True
                break

        if found is False:
            return -1
        if mid == len(self.__ann) - 1:
            return mid

        # We go further to look at the next localizations until they are different.
        while mid+1 < len(self.__ann) and \
                self.__ann[mid+1].get_highest_localization() == moment:
            mid += 1

        return mid

    # -----------------------------------------------------------------------

    def is_superset(self, other):
        """Return True if this tier contains all points of the other tier.

        :param other: (sppasTier)
        :returns: Boolean

        """
        if len(other) == 0:
            return True

        tier_points = self.get_all_points()
        other_points = other.get_all_points()

        for op in other_points:
            if op not in tier_points:
                return False

        return True

    # ------------------------------------------------------------------------

    def near(self, moment, direction=1):
        """Search for the annotation whose localization is closest.

        Search for the nearest localization to the given moment into a
        given direction.

        :param moment: (sppasPoint)
        :param direction: (int)
                - nearest 0
                - nereast forward 1
                - nereast backward -1

        """
        if len(self.__ann) == 0:
            return -1
        if len(self.__ann) == 1:
            return 0

        index = self.__find(moment)
        if index == -1:
            return -1

        a = self.__ann[index]

        # forward
        if direction == 1:
            if moment <= a.get_lowest_localization():
                return index
            if index + 1 < len(self.__ann):
                return index + 1
            return -1

        # backward
        elif direction == -1:
            if moment >= a.get_highest_localization():
                return index
            if index-1 >= 0:
                return index-1
            return -1

        # direction == 0 (select the nearest)

        # if time is during an annotation
        a = self.__ann[index]
        if a.get_lowest_localization() <= moment <= a.get_highest_localization():
            return index

        # then, the nearest is either the current or the next annotation
        _next = index + 1
        if _next >= len(self.__ann):
            # no next
            return index

        time = moment.get_midpoint()
        prev_time = self.__ann[index].get_highest_localization().get_midpoint()
        next_time = self.__ann[_next].get_lowest_localization().get_midpoint()
        if abs(time - prev_time) > abs(next_time - time):
            return _next

        return index

    # -----------------------------------------------------------------------
    # Labels
    # -----------------------------------------------------------------------

    def is_string(self):
        """All label tags are string or unicode or None."""
        if len(self.__ann) == 0:
            return False

        for ann in self.__ann:
            if ann.is_labelled() is True:
                return ann.label_is_string()

        return False

    # -----------------------------------------------------------------------

    def is_float(self):
        """All label tags are float values or None."""
        if len(self.__ann) == 0:
            return False

        for ann in self.__ann:
            if ann.is_labelled() is True:
                return ann.label_is_float()

        return False

    # -----------------------------------------------------------------------

    def is_int(self):
        """All label tags are integer values or None."""
        if len(self.__ann) == 0:
            return False

        for ann in self.__ann:
            if ann.is_labelled() is True:
                return ann.label_is_int()

        return False

    # -----------------------------------------------------------------------

    def is_bool(self):
        """All label tags are boolean values or None."""
        if len(self.__ann) == 0:
            return False

        for ann in self.__ann:
            if ann.is_labelled() is True:
                return ann.label_is_bool()

        return False

    # -----------------------------------------------------------------------

    def get_labels_type(self):
        """Return the current type of labels, or an empty string."""
        if len(self.__ann) == 0:
            return ""

        for ann in self.__ann:
            if ann.is_labelled() is True:
                return ann.get_label_type()

        return ""

    # -----------------------------------------------------------------------

    def get_nb_filled_labels(self):
        """Return the number annotation with a filled label."""
        nb = 0
        for ann in self.__ann:
            if ann.is_labelled() is True:
                nb += 1
        return nb

    # -----------------------------------------------------------------------
    # Annotation validation
    # -----------------------------------------------------------------------

    def validate(self):
        if self.__parent is not None:
            self.__parent.validate_hierarchy(self)

    # -----------------------------------------------------------------------

    def validate_annotation(self, annotation):
        """Validate the annotation and set its parent to this tier.

        :param annotation: (sppasAnnotation)
        :raises: AnnDataTypeError, CtrlVocabContainsError, \
        HierarchyContainsError, HierarchyTypeError

        """
        # Check instance:
        if isinstance(annotation, sppasAnnotation) is False:
            raise AnnDataTypeError(annotation, "sppasAnnotation")

        # Check if annotation is relevant for this tier
        #  - same localization type?
        #  - same label type?
        #  - label consistency
        #  - location consistency
        if len(self.__ann) > 0:
            if annotation.location_is_point() is True and self.is_point() is False:
                raise AnnDataTypeError(str(annotation)+" (sppasPoint)", "sppasInterval")
            if annotation.location_is_interval() is True and self.is_interval() is False:
                raise AnnDataTypeError(str(annotation)+" (sppasInterval)", "sppasPoint")
            if annotation.location_is_disjoint() is True and self.is_disjoint() is False:
                raise AnnDataTypeError(annotation, "sppasDisjoint")

        # Assigning a parent will validate the label and the location
        annotation.set_parent(self)

    # -----------------------------------------------------------------------

    def validate_annotation_label(self, label):
        """Validate a label.

        :param label: (sppasLabel)
        :raises: CtrlVocabContainsError

        """
        # Check if controlled vocabulary
        if self.__ctrl_vocab is not None:
            for tag, score in label:
                if tag.is_empty() is False and self.__ctrl_vocab.contains(tag) is False:
                    raise CtrlVocabContainsError(tag)

        # in this tier, no typed tag is already assigned.
        if (self.is_bool() or self.is_float() or self.is_int() or self.is_string()) is False:
            return

        # check if the current label has the same tag type than
        # the already defined ones.
        if label.is_tagged():
            if label.get_type() != self.get_labels_type():
                raise AnnDataTypeError(label, self.get_labels_type())

    # -----------------------------------------------------------------------

    def validate_annotation_location(self, location):
        """Ask the parent to validate a location.

        :param location: (sppasLocation)
        :raises: AnnDataTypeError, HierarchyContainsError, HierarchyTypeError

        """
        if self.__parent is not None:
            self.__parent.validate_annotation_location(self, location)

    # -----------------------------------------------------------------------

    def get_annotation(self, identifier):
        """Find an annotation from its metadata 'id'.

        :param identifier: (str) Metadata 'id' of an annotation.
        :returns: sppasAnnotation or None

        """
        for a in self:
            if a.get_meta('id') == identifier:
                return a
        return None

    # -----------------------------------------------------------------------

    def get_annotation_index(self, ann):
        """Find an annotation.

        :param ann: (sppasAnnotation)
        :returns: (int) -1 if not found

        """
        if self.is_point():
            return self.index(ann.get_highest_localization())

        else:
            i1 = self.lindex(ann.get_lowest_localization())
            i2 = self.rindex(ann.get_highest_localization())
            for i in range(i1, i2+1):
                ai = self.__ann[i]
                if ai is ann:
                    return i
                if ai.get_id() == ann.get_id():
                    return i

        return -1

    # -----------------------------------------------------------------------
    # Utils
    # -----------------------------------------------------------------------

    def create_ctrl_vocab(self, name=None):
        """Create the controlled vocabulary from annotation labels.

        Create (or re-create) the controlled vocabulary from the list of
        already existing annotation labels.
        The current controlled vocabulary is deleted.

        :param name: (str) Name of the controlled vocabulary. \
        The name of the tier is used by default.

        """
        if name is None:
            name = self.__name
        self.__ctrl_vocab = sppasCtrlVocab(name)

        for ann in self.__ann:
            for label in ann.get_labels():
                if label.is_tagged():
                    for tag, score in label:
                        self.__ctrl_vocab.add(tag)

    # -----------------------------------------------------------------------

    def export_to_intervals(self, separators):
        """Create a tier with the consecutive filled intervals.

        Return an empty tier if 'self' is not of type "interval".
        The created intervals are not filled.

        :param separators: (list)
        :returns: (sppasTier)

        """
        intervals = sppasTier("intervals")
        if self.is_interval() is False:
            return intervals

        begin = self.get_first_point()
        end = begin
        prev_ann = None

        for ann in self.__ann:
            tag = None
            if ann.label_is_filled():
                tag = ann.get_best_tag()

            if prev_ann is not None:
                # if no tag or stop tag or hole between prev_ann and ann
                if tag is None or \
                   tag.get_typed_content() in separators or \
                   prev_ann.get_highest_localization() < ann.get_lowest_localization():
                    if end > begin:
                        intervals.create_annotation(sppasLocation(
                              sppasInterval(begin,
                                            prev_ann.get_highest_localization())))

                    if tag is None or tag.get_typed_content() in separators:
                        begin = ann.get_highest_localization()
                    else:
                        begin = ann.get_lowest_localization()
            else:
                # phonemes can start with a non-labelled interval!
                if tag is None or tag.get_typed_content() in separators:
                    begin = ann.get_highest_localization()

            end = ann.get_highest_localization()
            prev_ann = ann

        if end > begin:
            ann = self.__ann[-1]
            end = ann.get_highest_localization()
            intervals.create_annotation(sppasLocation(sppasInterval(begin, end)))

        return intervals

    # -----------------------------------------------------------------------

    def export_unfilled(self):
        """Create a tier with the unlabelled/unfilled intervals.

        Only for tiers of type Interval.
        It represents the "NOT tier", ie where this tier is not annotated.

        IMPORTANT: Never tested with overlapped annotations,
        actually not tested at all (but used in the plugin StatGroups).

        :return: (sppasTier) or None

        """
        if self.is_empty() is True:
            return None
        if self.is_interval() is False:
            return None

        intervals = self.export_to_intervals([])
        not_intervals = sppasTier("NotIntervals")
        if intervals.is_empty():
            not_intervals.create_annotation(
                sppasLocation(sppasInterval(self.get_first_point(),
                                            self.get_last_point()))
            )
            return not_intervals

        # first "unfilled" interval
        begin = self.__ann[0].get_lowest_localization()
        prev_ann = intervals[0]
        prev_begin = prev_ann.get_lowest_localization()
        if prev_begin > begin:
            not_intervals.create_annotation(
                sppasLocation(sppasInterval(begin, prev_begin))
            )

        # holes
        for i in range(1, len(intervals)):
            prev_end = prev_ann.get_highest_localization()
            ann = intervals[i]
            begin = ann.get_lowest_localization()
            if begin > prev_end:
                not_intervals.create_annotation(
                    sppasLocation(sppasInterval(prev_end, begin))
                )
            prev_ann = ann

        # last "unfilled" interval
        end = self.__ann[-1].get_highest_localization()
        prev_end = intervals[-1].get_highest_localization()
        if prev_end < end:
            not_intervals.create_annotation(
                sppasLocation(sppasInterval(prev_end, end))
            )

        return not_intervals

    # -----------------------------------------------------------------------

    def fit(self, other):
        """Select then slice or extend annotations to fit in other tier.

        Keep only the annotations of self that have some overlapping time
        with the given other tier and slice the localization of
        such selected annotations to exactly match those of the other tier.

        Example:

                 0   1   2   3   4   5   6   7   8   9  10  11  12  13  14
        tier1:         |_a_|_b_|       |_c_|   |_d_|     |_e_|       |f|
        tier2:           |_w_|       |_______x_______|     |_y_| |_z_|

        tier1.fit(tier2) result is:
                         |a|b|         |_c_|   |_d_|       |e|

        tier2.fit(tier1) result is:
                         |w|w|         |_x_|   |_x_|       |y|

        :param other: (sppasTier)
        :return: (sppasTier)

        """
        ft = sppasTier(self.__name + "-inter-" + other.get_name())
        for ann in other:
            b = ann.get_lowest_localization()
            e = ann.get_highest_localization()
            found_anns = self.find(b, e, overlaps=True)

            if len(found_anns) == 1:
                labels = list()
                for la in found_anns[0].get_labels():
                    labels.append(la.copy())
                # If there is only one annotation of self that is matching
                # the annotation of other. fit result is [max begin ; min end]
                bf = max(b, found_anns[0].get_lowest_localization())
                ef = min(e, found_anns[0].get_highest_localization())
                ft.create_annotation(sppasLocation(sppasInterval(bf.copy(), ef.copy())), labels)

            elif len(found_anns) > 1:
                # If there are annotations of self that are matching the
                # annotation of other. first and last can be sliced.
                for i, ao in enumerate(found_anns):
                    labels = list()
                    for la in ao.get_labels():
                        labels.append(la.copy())

                    if ao is found_anns[0]:
                        bf = max(b, ao.get_lowest_localization())
                        location = sppasLocation(sppasInterval(bf.copy(), ao.get_highest_localization().copy()))

                    elif ao is found_anns[-1]:
                        ef = min(e, ao.get_highest_localization())
                        location = sppasLocation(sppasInterval(ao.get_lowest_localization().copy(), ef.copy()))

                    else:
                        location = ao.get_location().copy()

                    ft.create_annotation(location, labels)

        return ft

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __find(self, x):
        """Return the index of the annotation whose moment value contains x.

        :param x: (sppasPoint)

        """
        if len(self.__ann) == 0:
            return -1
        if len(self.__ann) == 1:
            return 0
        if x > self.__ann[-1].get_highest_localization():
            return len(self.__ann) - 1

        is_point = self.is_point()
        lo = 0
        hi = len(self.__ann)  # - 1
        mid = (lo + hi) // 2

        while lo < hi:

            mid = (lo + hi) // 2
            a = self.__ann[mid]
            if is_point is True:
                p = a.get_location().get_best()
                if p == x:
                    return mid
                if x < p:
                    hi = mid
                else:
                    lo = mid + 1
            else:  # Interval or Disjoint
                b = a.get_lowest_localization()
                e = a.get_highest_localization()
                if b <= x < e:
                    return mid

                if x < e:
                    hi = mid
                else:
                    lo = mid + 1

        # direction was previously used by near...
        # We failed to find an annotation at time=x. return the closest...
        # if direction == 1:
        #     return min(hi, len(self.__ann) - 1)
        # if direction == -1:
        #     return lo
        return mid

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __iter__(self):
        for a in self.__ann:
            yield a

    def __getitem__(self, i):
        return self.__ann[i]

    def __len__(self):
        return len(self.__ann)

    def __contains__(self, value):
        """Value can be either an annotation or an annotation identifier."""
        if isinstance(value, sppasAnnotation):
            return value in self.__ann
        else:
            for a in self.__ann:
                if a.get_id() == value:
                    return True
        return False

    # -----------------------------------------------------------------------

    def __hash__(self):
        # use the hashcode of self identifier since that is used
        # for equality checks as well, like "tier in my_dict".
        # not required by Python 2.7 but necessary for Python 3.4+
        return hash(self.get_id())

