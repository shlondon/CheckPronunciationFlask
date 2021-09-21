# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.kidsbuffer.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Video buffer with coords and known identifiers.

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

from sppas.src.config import sppasTypeError
from sppas.src.videodata import sppasCoordsVideoBuffer

# ---------------------------------------------------------------------------


class sppasKidsVideoBuffer(sppasCoordsVideoBuffer):
    """A video buffer with both a list of coordinates and their identifiers.

    """

    def __init__(self, video=None, size=-1):
        """Create a new instance.

        :param video: (str) The video filename
        :param size: (int) Number of images of the buffer or -1 for auto

        """
        super(sppasKidsVideoBuffer, self).__init__(video, size=size)

        # The list of list of identifiers for each image of the buffer.
        # This list of identifiers of an image has the same length than the
        # list of coordinates of the same image.
        self.__ids = list()
        self.__init_ids()

    # -----------------------------------------------------------------------

    def __init_ids(self):
        # The list of list of identifiers
        self.__ids = list()
        for i in range(self.get_buffer_size()):
            self.__ids.append(list())

    # -----------------------------------------------------------------------

    def reset(self):
        """Override. Reset all the info related to the buffer content."""
        sppasCoordsVideoBuffer.reset(self)
        self.__init_ids()

    # -----------------------------------------------------------------------

    def next(self):
        """Override. Fill in the buffer with the next images & reset ids.

        """
        ret = sppasCoordsVideoBuffer.next(self)
        self.__init_ids()
        return ret

    # -----------------------------------------------------------------------

    def get_ids(self, buffer_index=None):
        """Return the identifiers of all detected coords of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :return: (list of identifiers)

        """
        if buffer_index is not None:
            buffer_index = self.check_buffer_index(buffer_index)
            return self.__ids[buffer_index]
        else:
            assert len(self.__ids) == self.__len__()
            return self.__ids

    # -----------------------------------------------------------------------

    def set_ids(self, buffer_index, ids):
        """Set the coord identifiers of a given image index.

        The number of identifiers must match the number of coords.

        :param buffer_index: (int) Index of the image in the buffer
        :param ids: (list of identifiers) A list of identifiers

        """
        coords_i = self.get_coordinates(buffer_index)
        if isinstance(ids, (list, tuple)) is True:
            if len(coords_i) != len(ids):
                raise ValueError("Expected {:d} identifiers. Got {:d} instead."
                                 "".format(len(coords_i), len(ids)))
            self.__ids[buffer_index] = ids

        else:
            raise sppasTypeError(type(ids), "(list, tuple)")

    # -----------------------------------------------------------------------

    def get_id(self, buffer_index, coord_index):
        """Return the identifier of a coord of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Index of the coords
        :return: (Sights)

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= coord_index < len(self.__ids[buffer_index]):
            return self.__ids[buffer_index][coord_index]

        raise ValueError("Invalid index value.")

    # -----------------------------------------------------------------------

    def set_id(self, buffer_index, coord_index, identifier):
        """Set the id to coordinate of a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Index of the coordinates for this id
        :param identifier: (any) Any relevant information

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= coord_index < len(self.__ids[buffer_index]):
            self.__ids[buffer_index][coord_index] = identifier
        else:
            raise ValueError("Face index error {}".format(coord_index))

    # -----------------------------------------------------------------------

    def set_coordinates(self, buffer_index, coords):
        """Set the coordinates to a given image index.

        Override to invalidate the corresponding identifiers.

        :param buffer_index: (int) Index of the image in the buffer
        :param coords: (list of sppasCoords) Set the list of coords

        """
        sppasCoordsVideoBuffer.set_coordinates(self, buffer_index, coords)
        self.__ids[buffer_index] = [str(i+1) for i in range(len(coords))]

    # -----------------------------------------------------------------------

    def append_coordinate(self, buffer_index, coord):
        """Override. Append the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Append the given coord
        :return: (int) Index of the new coordinate

        """
        sppasCoordsVideoBuffer.append_coordinate(self, buffer_index, coord)
        self.__ids[buffer_index].append(str(len(self.get_coordinates(buffer_index))))
        return len(self.__ids[buffer_index])-1

    # -----------------------------------------------------------------------

    def remove_coordinate(self, buffer_index, coord):
        """Override. Remove the coordinates to a given image index.

        Override to remove the identifier too.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Remove the given coord

        """
        coord_idx = self.index_coordinate(buffer_index, coord)
        sppasCoordsVideoBuffer.pop_coordinate(self, buffer_index, coord_idx)
        self.__ids[buffer_index].pop(coord_idx)

    # -----------------------------------------------------------------------

    def pop_coordinate(self, buffer_index, coord_index):
        """Override. Remove the coordinates to a given image index.

        Override to pop the identifier too.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Pop the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)
        sppasCoordsVideoBuffer.pop_coordinate(self, buffer_index, coord_index)
        self.__ids[buffer_index].pop(coord_index)

    # -----------------------------------------------------------------------

    def get_id_coordinate(self, buffer_index, identifier):
        """Return the coordinate of a given identifier in a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param identifier: (int) Identifier to search
        :return: (sppasCoords) Coordinates or None

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if identifier in self.__ids[buffer_index]:
            coord_idx = self.__ids[buffer_index].index(identifier)
            return self.get_coordinate(buffer_index, coord_idx)

        return None
