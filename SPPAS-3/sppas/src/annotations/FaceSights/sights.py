# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.sights.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Data structure to store the 68 sights of a face.

.. _This file is part of SPPAS: http://www.sppas.org/
..
    ---------------------------------------------------------------------

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

    ---------------------------------------------------------------------

"""

import codecs

from sppas.src.config import NegativeValueError
from sppas.src.config import IndexRangeException
from sppas.src.config import sppasTypeError
from sppas.src.imgdata import sppasCoords
from sppas.src.imgdata import sppasCoordsImageWriter

# ---------------------------------------------------------------------------


class Sights(object):
    """Data structure to store sights.

    This class is storing nb sights; each sight is made of 3 values:
        - x: coordinate on the x axis, initialized to 0
        - y: coordinate on the y axis, initialized to 0
        - an optional confidence score, initialized to None

    Notice that each of the sight parameter is stored into a list of 'nb'
    values, instead of storing a single list of 'nb' lists of values:

    - 2 lists of 'nb' int and 1 of float = [x1,x2,...] [y1,y2,...] [s1,s2,...]
        3*64 + 2*68*24 + 1*68*24 = 5088
    - 1 list of 'nb' lists of 2 int and 1 float: [[x1,y1,s1], [x2,y2,s2]...]
        64 + 68*64 + 2*68*24 + 1*68*24 = 9312

    """

    def __init__(self, nb=68):
        """Create a new instance.

        :param nb: (int) Number of expected sights.

        """
        # Number of sights to store
        self.__nb = sppasCoords.to_dtype(nb, int, unsigned=True)

        # Axis values
        self.__x = [0]*nb
        self.__y = [0]*nb
        # Confidence scores -- save memory when there are not used.
        self.__confidence = None

    # -----------------------------------------------------------------------

    def copy(self):
        """Return a deep copy of the current Sights()."""
        copied = Sights(nb=self.__nb)
        for i in range(self.__nb):
            x, y, s = self.get_sight(i)
            copied.set_sight(i, x, y, s)
        return copied

    # -----------------------------------------------------------------------

    def get_x(self):
        """Return the list of x values."""
        # returning self.__x allows it to be modified: a list is mutable.
        # here we return a copy in a tuple so self.__x won't change.
        return tuple(self.__x)

    # -----------------------------------------------------------------------

    def get_y(self):
        """Return the list of y values."""
        return tuple(self.__y)

    # -----------------------------------------------------------------------

    def get_s(self):
        """Return the list of confidence score values or None."""
        if self.__confidence is None:
            return None
        return tuple(self.__confidence)

    # -----------------------------------------------------------------------

    def get_sight(self, idx):
        """Return the (x, y, s) of the given sight.

        :param idx: (int) Index of the sight
        :return: tuple(x, y, confidence)

        """
        score = self.get_score(idx)
        return self.__x[idx], self.__y[idx], score

    # -----------------------------------------------------------------------

    def set_sight(self, idx, x, y, s=None):
        """Set the sight at the given index.

        :param idx: (int) Index of the sight
        :param x: (int) pixel position on the x axis (width)
        :param y: (int) pixel position on the y axis (height)
        :param s: (float or None) An optional confidence score

        """
        # Check the given parameters
        idx = self.check_index(idx)
        x = sppasCoords.to_dtype(x, int, unsigned=True)
        y = sppasCoords.to_dtype(y, int, unsigned=True)

        # Assign values to our data structures
        self.__x[idx] = x
        self.__y[idx] = y
        self.set_score(idx, s)

    # -----------------------------------------------------------------------

    def get_score(self, idx=None):
        """Return the score of the sight at the given index or None.

        :param idx: (int) Index of the sight or None to get the average score
        :return: (int or None)

        """
        if self.__confidence is None:
            return None

        if idx is not None:
            idx = self.check_index(idx)
            return self.__confidence[idx]
        else:
            values = [v for v in self.__confidence if v is not None]
            if len(values) == 0:
                return None
            return sum(values) / len(values)

    # -----------------------------------------------------------------------

    def set_score(self, idx, s):
        """Set a score to the sight at the given index.

        :param idx: (int) Index of the sight
        :param s: (float or None) An optional confidence score

        """
        idx = self.check_index(idx)
        # If a score is assigned
        if s is not None:
            s = sppasCoords.to_dtype(s, float, unsigned=False)
            if self.__confidence is None:
                # hum... we never assigned a score... create the list now
                self.__confidence = [None] * self.__nb
            self.__confidence[idx] = s
        else:
            if self.__confidence is not None:
                # A score is not set but we already have some. Clear the
                # one that is already existing.
                self.__confidence[idx] = None

    # -----------------------------------------------------------------------

    def check_index(self, value):
        """Raise an exception if the given index is not valid.

        :param value: (int)
        :raise: sppasTypeError, NegativeValueError, IndexRangeException

        """
        # Check if the given value is an integer
        try:
            value = int(value)
        except ValueError:
            raise sppasTypeError(value, "int")

        # Check if the given value is in the range [0,nb]
        if value < 0:
            raise NegativeValueError(value)
        if self.__nb < value:
            raise IndexRangeException(value, 0, self.__nb)

        # The given value is good
        return value

    # -----------------------------------------------------------------------

    def intermediate(self, other):
        """Return the sights with the intermediate positions.

        :param other: (Sights)
        :return: (Sights)

        """
        if isinstance(other, Sights) is False:
            raise sppasTypeError(other, "Sights")

        if len(other) != self.__nb:
            raise ValueError("Intermediate estimation expected {:d} sights. "
                             "Got {:d} instead.".format(self.__nb, len(other)))
        s = Sights(self.__nb)
        i = 0
        for s1, s2 in zip(self, other):  # s1=(x1,y1,c1) and s2=(x2,y2,c2)
            # estimate the middle point
            x = s1[0] + ((s2[0] - s1[0]) // 2)
            y = s1[1] + ((s2[1] - s1[1]) // 2)
            # estimate the average score
            c = None
            if s1[2] is not None and s2[2] is not None:
                c = (s1[2] + s2[2]) / 2.
            # Then set the sight position and score
            s.set_sight(i, x, y, c)
            i += 1

        return s

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        s = ""
        for i in range(self.__nb):
            s += "({:d},{:d}".format(self.__x[i], self.__y[i])
            if self.__confidence is not None:
                if self.__confidence[i] is not None:
                    s += ": {:f}".format(self.__confidence[i])
            s += ") "
        return s

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

    # ------------------------------------------------------------------------

    def __len__(self):
        """Return the number of sights."""
        return self.__nb

    # ------------------------------------------------------------------------

    def __iter__(self):
        """Browse the current sights."""
        for i in range(self.__nb):
            yield self.get_sight(i)

    # ------------------------------------------------------------------------

    def __getitem__(self, item):
        if isinstance(item, slice):
            # Get the start, stop, and step from the slice
            return [self.get_sight(ii) for ii in range(*item.indices(len(self)))]

        return self.get_sight(item)

    # -----------------------------------------------------------------------

    def __contains__(self, other):
        """Return true if value in sights -- score is ignored.

        :param other: a list/tuple of (x,y,...)

        """
        if isinstance(other, (list, tuple)) is False:
            return False
        if len(other) < 2:
            return False

        for i in range(self.__nb):
            if self.__x[i] == other[0] and self.__y[i] == other[1]:
                return True
        return False

# ---------------------------------------------------------------------------


class sppasImageSightsReader(object):
    """Read&create sights from a CSV file.

    Currently unused: To be tested.

    """

    def __init__(self, csv_file):
        """Set the list of sights defined in the given file.

        :param csv_file: sights from a sppasSightsImageWriter

        """
        self.sights = list()
        with codecs.open(csv_file, "r") as csv:
            lines = csv.readlines()

        if len(lines) > 0:
            for line in lines:
                content = line.split(";")
                # column to indicate a success: 1 if yes
                if content[2] == "1":
                    # number of sight values
                    nb = int(content[3])
                    s = Sights(nb)
                    # extract all (x, y, score)
                    for i in range(3, 3+nb):
                        x = content[i]
                        y = content[i+nb]
                        if len(content) > (3+(2*nb)):
                            score = content[i+(2*nb)]
                        else:
                            score = None
                        s.set_sight(i, x, y, score)

                    self.sights.append(s)

# ---------------------------------------------------------------------------


class sppasSightsImageWriter(sppasCoordsImageWriter):
    """Write an image and optionally sights into files.

    """

    def __init__(self):
        """Create a new sppasSightsImageWriter instance.

        Write the given image in the given filename.
        Parts of the image can be extracted in separate image files.
        Output images can be resized.
        Sights can be drawn in any of such output images.

        """
        super(sppasSightsImageWriter, self).__init__()

    # -----------------------------------------------------------------------

    @staticmethod
    def write_coords(fd, coords, sep=";"):
        """Write sights in the given stream.

        :param fd: (Stream) File descriptor, String descriptor, stdout, etc
        :param coords: (Sights) Sights to write in other columns.
        :param sep: (char) CSV separator

        """
        if coords is None:
            # write un-success
            fd.write("none{:s}0{:s}".format(sep, sep))
            return 0

        # write the average score, if we have one
        avg_score = coords.get_score()
        if avg_score is None:
            fd.write("none{:s}".format(sep))
        else:
            fd.write("{:f}{:s}".format(avg_score, sep))

        # then write success, then coords
        if len(coords) > 0:
            # write success -- like in OpenFace2 CSV results
            fd.write("1{:s}".format(sep))

            # number of sights
            fd.write("{:d}{:s}".format(len(coords), sep))

            # write all x values
            for x in coords.get_x():
                fd.write("{:d}{:s}".format(x, sep))

            # write all y values
            for y in coords.get_y():
                fd.write("{:d}{:s}".format(y, sep))

            # write confidence scores if they exist
            scores = coords.get_s()
            if scores is not None:
                for s in scores:
                    if s is None:
                        fd.write("none{:s}".format(sep))
                    else:
                        fd.write("{:f}{:s}".format(s, sep))

        else:
            # write success
            fd.write("0{:s}".format(sep))
            return 0

        return 1

    # -----------------------------------------------------------------------

    def tag_coords(self, img, coords, pen_width, colors=list()):
        """Override to tag image for the given coords OR sights.

        :param img: (sppasImage) The image to write
        :param coords: (list of Sights) The sights of objects
        :param colors: List of (r,g,b) Tuple with RGB int values
        :return: (sppasImage)

        """
        if isinstance(coords, (list, tuple)) is False:
            raise sppasTypeError(type(coords), "list, tuple")

        for i, c in enumerate(coords):
            if c is None:
                continue

            # Get the i-th color
            if len(coords) != len(colors):
                n = len(self._colors)
                r = self._colors['r'][i % n]
                g = self._colors['g'][i % n]
                b = self._colors['b'][i % n]
                rgb = (r, g, b)
            else:
                rgb = colors[i]

            if isinstance(c, Sights):
                # Draw the sights -- the score of each sight is ignored
                for sight in c:
                    img.surround_point(sight, color=rgb, thickness=pen_width)

            elif isinstance(c, sppasCoords):
                # Surround the coords with a square -- score is ignored
                img.surround_coord(c, color=rgb, thickness=pen_width)

        return img
