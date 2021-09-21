# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceSights.videosights.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Data structure to manage the 68 sights on faces of a video.

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

import os
import logging
import codecs

from sppas.src.config import sppasTypeError
from sppas.src.imgdata import sppasCoords
from sppas.src.videodata import sppasCoordsVideoBuffer
from sppas.src.videodata import sppasCoordsVideoWriter

from .sights import Sights
from .sights import sppasSightsImageWriter

# ---------------------------------------------------------------------------


class sppasSightsVideoBuffer(sppasCoordsVideoBuffer):
    """A video buffer with lists of coordinates, identifiers and sights.

    """

    def __init__(self,
                 video=None,
                 size=-1):
        """Create a new instance.

        :param video: (str) The video filename
        :param size: (int) Number of images of the buffer or -1 for auto

        """
        super(sppasSightsVideoBuffer, self).__init__(video, size=size)

        # The list of list of Sights instances() and face identifiers
        # By default, the identifier is the face number
        self.__sights = list()
        self.__ids = list()
        self.__init_sights()

    # -----------------------------------------------------------------------

    def __init_sights(self):
        # The list of list of identifiers
        self.__ids = list()
        # The list of list of sights
        self.__sights = list()
        for i in range(self.get_buffer_size()):
            self.__sights.append(list())
            self.__ids.append(list())

    # -----------------------------------------------------------------------

    def reset(self):
        """Override. Reset all the info related to the buffer content."""
        sppasCoordsVideoBuffer.reset(self)
        self.__init_sights()

    # -----------------------------------------------------------------------

    def next(self):
        """Override. Fill in the buffer with the next images & reset sights.

        """
        ret = sppasCoordsVideoBuffer.next(self)
        self.__init_sights()
        return ret

    # -----------------------------------------------------------------------

    def get_ids(self, buffer_index=None):
        """Return the identifiers of all faces of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :return: (list of identifiers)

        """
        if buffer_index is not None:
            buffer_index = self.check_buffer_index(buffer_index)
            return self.__ids[buffer_index]
        else:
            if len(self.__ids) != self.__len__():
                raise ValueError("Identifiers were not properly associated to images of the buffer")
            return self.__ids

    # -----------------------------------------------------------------------

    def get_sights(self, buffer_index=None):
        """Return the sights of all faces of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :return: (list of Sights)

        """
        if buffer_index is not None:
            buffer_index = self.check_buffer_index(buffer_index)
            return self.__sights[buffer_index]
        else:
            if len(self.__sights) != self.__len__():
                raise ValueError("Sights were not properly associated to images of the buffer")
            return self.__sights

    # -----------------------------------------------------------------------

    def set_ids(self, buffer_index, ids):
        """Set the face identifiers of a given image index.

        The number of identifiers must match the number of faces.

        :param buffer_index: (int) Index of the image in the buffer
        :param ids: (list of identifiers) A list of face identifiers

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

    def set_sights(self, buffer_index, sights):
        """Set the sights to a given image index.

        The number of sights must match the number of faces.

        :param buffer_index: (int) Index of the image in the buffer
        :param sights: (list of Sights) Set the list of sights

        """
        coords_i = self.get_coordinates(buffer_index)

        if isinstance(sights, (list, tuple)) is True:
            if len(coords_i) != len(sights):
                raise ValueError("Expected {:d} sights. Got {:d} instead."
                                 "".format(len(coords_i), len(sights)))
            # Check if all sights items are correct
            checked = list()
            for c in sights:
                if c is None:
                    c = Sights()
                else:
                    if isinstance(c, Sights) is False:
                        raise sppasTypeError(c, "Sights")
                checked.append(c)

            # Set sights and identifiers
            self.__sights[buffer_index] = checked

        else:
            raise sppasTypeError(type(sights), "(list, tuple)")

    # -----------------------------------------------------------------------

    def get_sight(self, buffer_index, face_index):
        """Return the sights of a face of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param face_index: (int) Index of the face
        :return: (Sights)

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= face_index < len(self.__sights[buffer_index]):
            return self.__sights[buffer_index][face_index]

        raise ValueError("Invalid face index value.")

    # -----------------------------------------------------------------------

    def get_id(self, buffer_index, face_index):
        """Return the identifier of a face of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param face_index: (int) Index of the face
        :return: (Sights)

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= face_index < len(self.__ids[buffer_index]):
            return self.__ids[buffer_index][face_index]

        raise ValueError("Invalid face index value.")

    # -----------------------------------------------------------------------

    def set_sight(self, buffer_index, face_index, sight):
        """Set the sights to a face of a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param sight: (Sights) the given sight object

        """
        buffer_index = self.check_buffer_index(buffer_index)

        if isinstance(sight, Sights):
            if face_index < len(self.__sights[buffer_index]):
                self.__sights[buffer_index][face_index] = sight
            else:
                raise ValueError("face index error")
        else:
            raise sppasTypeError(sight, "Sights")

    # -----------------------------------------------------------------------

    def set_id(self, buffer_index, coords_index, identifier):
        """Set the id to coordinate of a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coords_index: (int) Index of the coordinates for this id
        :param identifier: (any) Any relevant information

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if coords_index < len(self.__ids[buffer_index]):
            self.__ids[buffer_index][coords_index] = identifier
        else:
            raise ValueError("Face index error {}".format(coords_index))

    # -----------------------------------------------------------------------

    def set_coordinates(self, buffer_index, coords):
        """Set the coordinates to a given image index.

        Override to invalidate the corresponding sights and identifiers.

        :param buffer_index: (int) Index of the image in the buffer
        :param coords: (list of sppasCoords) Set the list of coords

        """
        sppasCoordsVideoBuffer.set_coordinates(self, buffer_index, coords)
        self.__sights[buffer_index] = [None for i in range(len(coords))]
        self.__ids[buffer_index] = [str(i+1) for i in range(len(coords))]

    # -----------------------------------------------------------------------

    def append_coordinate(self, buffer_index, coord):
        """Override. Append the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Append the given coord
        :return: (int) Index of the new coordinate

        """
        sppasCoordsVideoBuffer.append_coordinate(self, buffer_index, coord)
        self.__sights[buffer_index].append(None)
        self.__ids[buffer_index].append(str(len(self.__sights)))
        return len(self.__sights[buffer_index])-1

    # -----------------------------------------------------------------------

    def remove_coordinate(self, buffer_index, coord):
        """Remove the coordinates to a given image index.

        Override to remove the sights and the identifier too.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Remove the given coord

        """
        face_idx = self.index_coordinate(buffer_index, coord)
        sppasCoordsVideoBuffer.pop_coordinate(self, buffer_index, face_idx)
        self.__sights[buffer_index].pop(face_idx)
        self.__ids[buffer_index].pop(face_idx)

    # -----------------------------------------------------------------------

    def pop_coordinate(self, buffer_index, coord_index):
        """Remove the coordinates to a given image index.

        Override to pop the sights and the identifier too.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Pop the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)
        sppasCoordsVideoBuffer.pop_coordinate(self, buffer_index, coord_index)
        self.__sights[buffer_index].pop(coord_index)
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

    # -----------------------------------------------------------------------

    def get_id_sight(self, buffer_index, identifier):
        """Return the sights of a given identifier in a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param identifier: (int) Identifier to search
        :return: (sppasCoords) Coordinates or None

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if identifier in self.__ids[buffer_index]:
            coord_idx = self.__ids[buffer_index].index(identifier)
            return self.get_sight(buffer_index, coord_idx)

        return None

# ---------------------------------------------------------------------------


class sppasSightsVideoReader(object):
    """Read&create list of coords and sights from a CSV file.

    The CSV file must have the following columns:

        - frame number
        - the index of the coords -- face_id in OpenFace2
        - timestamp
        - confidence         -- face detection
        - success            -- face detection
        - buffer number
        - index in the buffer
        - x, y, w, h
        - average confidence -- face landmark
        - success            -- face landmark
        - n                  -- number of sights
        - x_1 .. x_n
        - y_1 .. y_n
        - optionally score_1 .. score_n

    """

    def __init__(self, csv_file, separator=";"):
        """Set the list of coords & sights defined in the given file.

        :param csv_file: (str) coords&sights from a sppasSightsVideoWriter
        :param separator: (char) Columns separator in the CSV file

        """
        logging.info("Sights CSV file reader")
        self.coords = list()
        self.sights = list()
        self.ids = list()

        with codecs.open(csv_file, "r") as csv:
            lines = csv.readlines()

        if len(lines) > 0:
            for line in lines:
                columns = line.split(separator)

                # 1st coord = new image
                if int(columns[1]) in (0, 1):
                    self.coords.append(list())
                    self.sights.append(list())
                    self.ids.append(list())

                # columns[4] is 0=failed, 1=success -- face found or not
                if int(columns[4]) == 1 and len(columns) > 8:
                    # identifier (the face number by default)
                    name = columns[1]
                    self.ids[len(self.ids) - 1].append(name)
                    # coordinates
                    coord = sppasCoords(int(columns[5]),
                                        int(columns[6]),
                                        int(columns[7]),
                                        int(columns[8]),
                                        float(columns[3]))
                    self.coords[len(self.coords) - 1].append(coord)

                    # sights
                    # columns[11] is the average score of sights or "none"
                    # columns[12] is 0=failed, 1=success -- sights found or not
                    if len(columns) > 12 and int(columns[12]) == 1:
                        # number of sight values
                        nb = int(columns[13])
                        s = Sights(nb)
                        # extract all (x, y, score)
                        for i in range(14, 14+nb):
                            x = int(columns[i])
                            y = int(columns[i+nb])
                            if len(columns) > (14+(2*nb)):
                                score = float(columns[i+(2*nb)])
                            else:
                                score = None
                            s.set_sight(i-14, x, y, score)

                        self.sights[len(self.sights) - 1].append(s)
                    else:
                        self.sights[len(self.sights) - 1].append(None)

# ---------------------------------------------------------------------------


class sppasSightsVideoWriter(sppasCoordsVideoWriter):
    """Write a video and optionally coords/sights into files.

    """

    def __init__(self, image_writer=None):
        """Create a new instance.

        """
        super(sppasSightsVideoWriter, self).__init__()

        # Override
        self._img_writer = sppasSightsImageWriter()
        if image_writer is not None:
            if isinstance(image_writer, sppasSightsImageWriter) is True:
                self._img_writer = image_writer

        # new member: associate a color to a person
        self.__person_colors = dict()

    # -----------------------------------------------------------------------

    def write_coords(self, fd, video_buffer, buffer_idx, idx):
        """Override to write the coords AND sights AND ids into the stream.

        - frame number
        - the index of the coords -- face_id in OpenFace2
        - timestamp
        - confidence
        - success
        - buffer number
        - index in the buffer
         - x, y, w, h,
        - the nb of sights: 68
        - the 68 x values
        - the 68 y values
        - eventually, the 68 confidence scores

        :param fd: (Stream) File descriptor, String descriptor, stdout, etc
        :param video_buffer: (sppasCoordsVideoBuffer)
        :param buffer_idx: (int) Buffer number
        :param idx: (int) An integer to write

        """
        sep = self._img_writer.get_csv_sep()

        # Get the lists stored for the i-th image
        coords = video_buffer.get_coordinates(idx)
        sights = video_buffer.get_sights(idx)
        ids = video_buffer.get_ids(idx)
        frame_idx = (buffer_idx * video_buffer.get_buffer_size()) + idx

        # Write the coords&sights
        if len(coords) == 0:
            # the same as base class
            fd.write("{:d}{:s}".format(frame_idx + 1, sep))
            fd.write("0{:s}".format(sep))
            fd.write("{:.3f}{:s}".format(float(frame_idx) / self._fps, sep))
            fd.write("none{:s}".format(sep))
            fd.write("0{:s}".format(sep))
            fd.write("0{:s}0{:s}0{:s}0{:s}".format(sep, sep, sep, sep))
            fd.write("{:d}{:s}".format(buffer_idx + 1, sep))
            fd.write("{:d}{:s}".format(idx, sep))
            fd.write("\n")

        else:
            # write each coords/sights in a new line
            for j in range(len(coords)):
                fd.write("{:d}{:s}".format(frame_idx + 1, sep))
                if j < len(ids):
                    fd.write("{}{:s}".format(ids[j], sep))
                else:
                    fd.write("{:d}{:s}".format(j + 1, sep))
                fd.write("{:.3f}{:s}".format(float(frame_idx) / self._fps, sep))
                fd.write("{:f}{:s}".format(coords[j].get_confidence(), sep))
                fd.write("1{:s}".format(sep))
                fd.write("{:d}{:s}".format(coords[j].x, sep))
                fd.write("{:d}{:s}".format(coords[j].y, sep))
                fd.write("{:d}{:s}".format(coords[j].w, sep))
                fd.write("{:d}{:s}".format(coords[j].h, sep))
                fd.write("{:d}{:s}".format(buffer_idx+1, sep))
                fd.write("{:d}{:s}".format(idx, sep))
                if j < len(sights):
                    sppasSightsImageWriter.write_coords(fd, sights[j])
                fd.write("\n")

    # -----------------------------------------------------------------------

    def write_video(self, video_buffer, out_name, pattern):
        """Save the result in video format.

        :param video_buffer: (sppasImage) The image to write
        :param out_name: (str) The filename of the output video file
        :param pattern: (str) Pattern to add to cropped video filename(s)
        :return: list of newly created video file names

        """
        new_files = list()
        if self._img_writer.options.tag is False:
            logging.info("Tag option is not enabled. Nothing to do.")
            return new_files

        all_colors = self._img_writer.get_colors()
        iter_images = video_buffer.__iter__()
        for i in range(video_buffer.__len__()):
            image = next(iter_images)
            b, _ = video_buffer.get_buffer_range()

            # Get the list of sights stored for the i-th image
            sights = video_buffer.get_sights(i)
            coords = video_buffer.get_coordinates(i)
            person_ids = video_buffer.get_ids(i)

            # Create the sppasVideoWriter() if it wasn't already done.
            # An image is required to properly fix the video size.
            if self._tag_video_writer is None:
                self._tag_video_writer, fn = self.create_video_writer(out_name, image, pattern)
                new_files.append(fn)

            # fix the colors of these coords and sights
            colors = list()
            for person_id in person_ids:
                if person_id not in self.__person_colors:
                    # get a new color
                    idx = len(self.__person_colors)
                    n = len(all_colors['r'])
                    # Get the idx-th color
                    r = all_colors['r'][idx % n]
                    g = all_colors['g'][idx % n]
                    b = all_colors['b'][idx % n]
                    rgb = (r, g, b)
                    self.__person_colors[person_id] = rgb
                # append the color for this person
                colors.append(self.__person_colors[person_id])

            # Tag&write the image with squares at the coords,
            # with circled for sights and a rectangle with the name
            img = self._img_writer.tag_image(image, coords, colors)
            img = self._img_writer.tag_image(img, sights, colors)
            self._text_image(img, coords, person_ids, colors)
            self._tag_video_writer.write(img)

        return new_files

    # -----------------------------------------------------------------------

    def _text_image(self, img, coords, texts, colors):
        """Put texts at top of given coords with given colors."""
        for coord, text, color in zip(coords, texts, colors):
            c = sppasCoords(coord.x, coord.y, coord.w, coord.h // 5)
            img.surround_coord(c, color, -4, text)

    # -----------------------------------------------------------------------

    def _tag_and_crop(self, video_buffer, image, idx, img_name, folder, pattern):

        new_files = list()
        # Get the list of coordinates stored for the i-th image
        coords = video_buffer.get_coordinates(idx)
        sights = video_buffer.get_sights(idx)

        # Draw the sights on a copy of the original image
        img = self._img_writer.tag_image(image, sights)

        # Tag and write the image
        if self._img_writer.options.tag is True:
            # Save the image
            out_iname = os.path.join(folder, img_name + self._image_ext)
            img.write(out_iname)
            new_files.append(out_iname)

        # Crop the image and write cropped parts
        if self._img_writer.options.crop is True:
            # Browse through the coords to crop the image
            for j, c in enumerate(coords):

                # Create the image filename
                iname = img_name + "_" + str(j) + pattern + self._image_ext
                out_iname = os.path.join(folder, iname)

                # Crop the given image to the coordinates and
                # resize only if the option width or height is enabled
                img_crop = self._img_writer.crop_and_size_image(img, c)

                # Add the image to the folder
                img_crop.write(out_iname)
                new_files.append(out_iname)

        return new_files
