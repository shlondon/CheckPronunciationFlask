# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.imgdata.coordinates.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Data structure to represent an area with a confidence score.

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

from sppas.src.exceptions import sppasTypeError
from sppas.src.exceptions import IntervalRangeException
from .imgdataexc import ImageEastingError, ImageNorthingError
from .imgdataexc import ImageWidthError, ImageHeightError, ImageBoundError

# ---------------------------------------------------------------------------


class sppasCoords(object):
    """Class to illustrate coordinates of an area.

    A sppasCoords object represents the coordinates of an image.
    It has 5 parameters:

    - x: coordinate on the x axis
    - y: coordinate on the y axis
    - w: width of the visage
    - h: height of the visage
    - an optional confidence score

    :Example:

    >>> c = sppasCoords(143, 17, 150, 98, 0.7)
    >>> c.get_confidence()
    >>> 0.7
    >>> c.get_x()
    >>> 143
    >>> c.get_y()
    >>> 17
    >>> c.get_w()
    >>> 150
    >>> c.get_h()
    >>> 98

    """

    # 4K width multiplied by 4
    MAX_W = 15360

    # 4K height multiplied by 4
    MAX_H = 8640

    # -----------------------------------------------------------------------

    def __init__(self, x=0, y=0, w=0, h=0, confidence=None):
        """Create a new sppasCoords instance.

        Allows to represent a point (x,y), or a size(w,h) or both, with an
        optional confidence score ranging [0.0,1.0].

        :param x: (int) The x-axis value
        :param y: (int) The y-axis value
        :param w: (int) The width value
        :param h: (int) The height value
        :param confidence: (float) An optional confidence score ranging [0,1]

        """
        self.__x = 0
        self.__set_x(x)

        self.__y = 0
        self.__set_y(y)

        self.__w = 0
        self.__set_w(w)

        self.__h = 0
        self.__set_h(h)

        # Save memory by using None instead of float if confidence is not set
        self.__confidence = None
        self.set_confidence(confidence)

    # -----------------------------------------------------------------------

    @staticmethod
    def to_coords(coord):
        """Check the given coord and return it as a sppasCoords instance."""
        if isinstance(coord, sppasCoords) is False:
            if isinstance(coord, (tuple, list)) is True:
                if len(coord) == 2:
                    try:
                        # Given coordinates are representing a point
                        coord = sppasCoords(coord[0], coord[1], w=0, h=0)
                    except:
                        pass
                elif len(coord) == 3:
                    try:
                        # Given coordinates are representing a point with a score
                        coord = sppasCoords(coord[0], coord[1], 0, 0, coord[2])
                    except:
                        pass
                elif len(coord) == 4:
                    try:
                        # Given coordinates are representing an area (point+size)
                        coord = sppasCoords(coord[0], coord[1], coord[2], coord[3])
                    except:
                        pass
                elif len(coord) > 4:
                    try:
                        # Given coordinates are representing an area (point+size)
                        # with a confidence score
                        coord = sppasCoords(coord[0], coord[1], coord[2], coord[3], coord[4])
                    except:
                        pass

        if isinstance(coord, sppasCoords) is False:
            raise sppasTypeError(coord, "sppasCoords")

        return coord

    # -----------------------------------------------------------------------

    def get_confidence(self):
        """Return the confidence value (float)."""
        if self.__confidence is None:
            return 0.
        return self.__confidence

    # -----------------------------------------------------------------------

    def set_confidence(self, value):
        """Set confidence value.

        :param value: (float) The new confidence value ranging [0, 1].
        :raise: TypeError, ValueError

        """
        if value is None:
            self.__confidence = None
        else:
            value = self.to_dtype(value, dtype=float, unsigned=False)
            if value < 0. or value > 1.:
                raise IntervalRangeException(value, 0, 1)
            self.__confidence = value

    # -----------------------------------------------------------------------

    def get_x(self):
        """Return x-axis value (int)."""
        return self.__x

    # -----------------------------------------------------------------------

    def __set_x(self, value):
        """Set x-axis value.

        :param value: (int) The new x-axis value.
        :raise: TypeError, ValueError

        """
        value = self.to_dtype(value)
        if value > sppasCoords.MAX_W:
            raise IntervalRangeException(value, 0, sppasCoords.MAX_W)
        self.__x = value

    # -----------------------------------------------------------------------

    def get_y(self):
        """Return y-axis value (int)."""
        return self.__y

    # -----------------------------------------------------------------------

    def __set_y(self, value):
        """Set y-axis value.

        :param value: (int) The new y-axis value.
        :raise: TypeError, ValueError

        """
        value = self.to_dtype(value)
        if value > sppasCoords.MAX_H:
            raise IntervalRangeException(value, 0, sppasCoords.MAX_H)
        self.__y = value

    # -----------------------------------------------------------------------

    def get_w(self):
        """Return width value (int)."""
        return self.__w

    # -----------------------------------------------------------------------

    def __set_w(self, value):
        """Set width value.

        :param value: (int) The new width value.
        :raise: TypeError, ValueError

        """
        value = self.to_dtype(value)
        if value > sppasCoords.MAX_W:
            raise IntervalRangeException(value, 0, sppasCoords.MAX_W)
        self.__w = value

    # -----------------------------------------------------------------------

    def get_h(self):
        """Return height value (int)."""
        return self.__h

    # -----------------------------------------------------------------------

    def __set_h(self, value):
        """Set height value.

        :param value: (int) The new height value.
        :raise: TypeError, ValueError

        """
        value = self.to_dtype(value)
        if value > sppasCoords.MAX_H:
            raise IntervalRangeException(value, 0, sppasCoords.MAX_H)
        self.__h = value

    # -----------------------------------------------------------------------

    @staticmethod
    def to_dtype(value, dtype=int, unsigned=True):
        """Convert a value to int or raise the appropriate exception."""
        try:
            v = dtype(value)
            if dtype is int:
                value = int(round(value))
            else:
                value = v
            if isinstance(value, dtype) is False:
                raise sppasTypeError(value, str(dtype))
        except ValueError:
            raise sppasTypeError(value, str(dtype))

        if unsigned is True:
            if value < 0:
                raise sppasTypeError(value, "unsigned " + str(dtype))

        return value

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    x = property(get_x, __set_x)
    y = property(get_y, __set_y)
    w = property(get_w, __set_w)
    h = property(get_h, __set_h)

    # -----------------------------------------------------------------------
    # Methods to manipulate coordinates
    # -----------------------------------------------------------------------

    def scale(self, coeff, image=None):
        """Multiply width and height values with given coefficient value.

        :param coeff: (int) The value to multiply with.
        :param image: (numpy.ndarray or sppasImage) An image to check w, h.
        :returns: Returns the value of the shift to use on the x-axis,
        according to the value of the scale in order to keep the same center.
        :raise: TypeError, ScaleWidthError, ScaleHeightError

        """
        coeff = self.to_dtype(coeff, dtype=float, unsigned=False)
        new_w = int(float(self.__w) * coeff)
        new_h = int(float(self.__h) * coeff)

        # Check new values with the width and height of the given image
        if image is not None:
            (height, width) = image.shape[:2]
            if new_w > width:
                raise ImageWidthError(new_w, width)
            if new_h > height:
                raise ImageHeightError(new_h, height)

        shift_x = int(float(self.__w - new_w) / 2.)
        shift_y = int(float(self.__h - new_h) / 2.)
        self.__w = new_w
        self.__h = new_h
        return shift_x, shift_y

    # -----------------------------------------------------------------------

    def shift(self, x_value=0, y_value=0, image=None):
        """Shift position of (x,y) values.

        :param x_value: (int) The value to add to x-axis value.
        :param y_value: (int) The value to add to y-axis value.
        :param image: (numpy.ndarray or sppasImage) An image to check coords.
        :raise: TypeError

        """
        # Check and convert given shift values
        x_value = self.to_dtype(x_value, unsigned=False)
        y_value = self.to_dtype(y_value, unsigned=False)

        new_x = self.__x + x_value
        if new_x < 0:
            new_x = 0

        new_y = self.__y + y_value
        if new_y < 0:
            new_y = 0

        if image is not None:
            # Get the width and height of image
            (max_h, max_w) = image.shape[:2]
            if x_value > 0:
                if new_x > max_w:
                    raise ImageEastingError(new_x, max_w)
                elif new_x + self.__w > max_w:
                    raise ImageBoundError(new_x + self.__w, max_w)
            if y_value > 0:
                if new_y > max_h:
                    raise ImageNorthingError(new_y, max_h)
                elif new_y + self.__h > max_h:
                    raise ImageBoundError(new_y + self.__h, max_h)

        self.__x = new_x
        self.__y = new_y

    # -----------------------------------------------------------------------

    def copy(self):
        """Return a deep copy of the current sppasCoords."""
        return sppasCoords(self.__x, self.__y, self.__w, self.__h,
                           self.__confidence)

    # -----------------------------------------------------------------------

    def area(self):
        """Return the area of the rectangle."""
        return self.__w * self.__h

    # -----------------------------------------------------------------------

    def intersection_area(self, other):
        """Return the intersection area of two rectangles.

        :param other: (sppasCoords)

        """
        if isinstance(other, sppasCoords) is False:
            raise sppasTypeError(other, "sppasCoords")
        self_xmax = self.__x + self.__w
        other_xmax = other.x + other.w
        dx = min(self_xmax, other_xmax) - max(self.__x, other.x)

        self_ymax = self.__y + self.__h
        other_ymax = other.y + other.h
        dy = min(self_ymax, other_ymax) - max(self.__y, other.y)

        if dx >= 0 and dy >= 0:
            return dx * dy
        return 0

    # -----------------------------------------------------------------------

    def overlap(self, other):
        """Return the 2 percentage of overlaps.

        1. the overlapped area is overlapping other of XX percent of its area.
        2. the overlapped area is overlapping self of XX percent of my area.

        :param other: (sppasCoords)
        :returns: percentage of overlap of self in other and of other in self.

        """
        in_area = self.intersection_area(other)
        if in_area == 0:
            return 0., 0.
        my_area = float(self.area())
        other_area = float(other.area())
        return (in_area/other_area)*100., (in_area/my_area)*100.

    # -----------------------------------------------------------------------

    def intermediate(self, other):
        """Return the coordinates with the intermediate position and size.

        :param other: (sppasCoords)
        :return: (sppasCoords)

        """
        if isinstance(other, sppasCoords) is False:
            raise sppasTypeError(other, "Sights")

        # estimate the middle point
        x = self.__x + ((other.x - self.x) // 2)
        y = self.__y + ((other.y - self.y) // 2)
        # estimate the intermediate size
        w = (self.__w + other.w) // 2
        h = (self.__h + other.h) // 2
        # average score
        c = (self.get_confidence() + other.get_confidence()) / 2.

        return sppasCoords(x, y, w, h, c)

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        s = "({:d},{:d})".format(self.__x, self.__y)
        if self.__w > 0 or self.__h > 0:
            s += " ({:d},{:d})".format(self.__w, self.__h)
        if self.__confidence is not None:
            s += ": {:f}".format(self.__confidence)
        return s

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    # -----------------------------------------------------------------------

    def __eq__(self, other):
        """Return true if self equal other (except for confidence score)."""
        if isinstance(other, (list, tuple)):
            if len(other) >= 4:
                other = sppasCoords(other[0], other[1], other[2], other[3])
            else:
                return False
        if isinstance(other, sppasCoords) is False:
            return False
        if self.__x != other.x:
            return False
        if self.__y != other.y:
            return False
        if self.__w != other.w:
            return False
        if self.__h != other.h:
            return False
        return True

    # -----------------------------------------------------------------------

    def __ne__(self, other):
        return not self.__eq__(other)

    # -----------------------------------------------------------------------

    def __hash__(self):
        return hash((self.__x,
                     self.__y,
                     self.__w,
                     self.__h))

    # -----------------------------------------------------------------------

    def __contains__(self, item):
        """Return True if the coords contains the given item.

        Contains does not mean overlaps... If item overlaps, False is returned.

        :param item: (sppasCoords, tuple, list)

        """
        cc = sppasCoords.to_coords(item)
        if cc.w > self.__w:
            return False
        if cc.h > self.__h:
            return False

        if cc.x < self.__x:
            return False
        if cc.y < self.__y:
            return False

        if cc.x + cc.w > self.__x + self.w:
            return False
        if cc.y + cc.h > self.__y + self.h:
            return False

        return True
