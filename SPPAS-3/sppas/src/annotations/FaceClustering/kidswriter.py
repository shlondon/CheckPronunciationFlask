# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.annotations.FaceClustering.kidswriter.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Write coords and identifiers.

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

from sppas.src.imgdata import sppasCoords
from sppas.src.imgdata import sppasCoordsImageWriter
from sppas.src.videodata import sppasCoordsVideoWriter

# ---------------------------------------------------------------------------


class sppasKidsVideoReader(object):
    """Read&create list of coords and ids from a CSV file.

    The CSV file must have the following columns:

        - frame number
        - identifier
        - timestamp
        - confidence
        - success
        - buffer number
        - index in the buffer
        - x, y, w, h

    """

    def __init__(self, csv_file, separator=";"):
        """Set the list of coords & ids defined in the given file.

        :param csv_file: (str) coords&identifiers from a sppasKidsVideoWriter
        :param separator: (char) Columns separator in the CSV file

        """
        self.coords = list()
        self.ids = list()

        with codecs.open(csv_file, "r") as csv:
            lines = csv.readlines()

        if len(lines) > 0:
            for line in lines:
                columns = line.split(separator)

                # 1st coord = new image
                if int(columns[1]) in (0, 1):
                    self.coords.append(list())
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

# ---------------------------------------------------------------------------


class sppasKidsVideoWriter(sppasCoordsVideoWriter):
    """Write a video and optionally coords and ids into files.

    """

    def __init__(self, image_writer=None):
        """Create a new instance.

        """
        super(sppasKidsVideoWriter, self).__init__()

        # Override
        self._img_writer = sppasCoordsImageWriter()
        if image_writer is not None:
            if isinstance(image_writer, sppasCoordsImageWriter) is True:
                self._img_writer = image_writer

        # new member: associate a color to a person
        self.__person_colors = dict()

    # -----------------------------------------------------------------------

    def write_coords(self, fd, video_buffer, buffer_idx, idx):
        """Override to write the coords AND ids into the stream.

        - frame number
        - the identifier
        - timestamp
        - confidence
        - success
        - buffer number
        - index in the buffer
         - x, y, w, h,

        :param fd: (Stream) File descriptor, String descriptor, stdout, etc
        :param video_buffer: (sppasCoordsVideoBuffer)
        :param buffer_idx: (int) Buffer number
        :param idx: (int) An integer to write

        """
        sep = self._img_writer.get_csv_sep()

        # Get the lists stored for the i-th image
        coords = video_buffer.get_coordinates(idx)
        ids = video_buffer.get_ids(idx)
        frame_idx = (buffer_idx * video_buffer.get_buffer_size()) + idx

        # Write the coords & ids
        if len(coords) == 0:
            # no coords were assigned to this image
            # the same as base class, except for the identifier: none
            fd.write("{:d}{:s}".format(frame_idx + 1, sep))
            fd.write("none{:s}".format(sep))
            fd.write("{:.3f}{:s}".format(float(frame_idx) / self._fps, sep))
            fd.write("none{:s}".format(sep))
            fd.write("0{:s}".format(sep))
            fd.write("0{:s}0{:s}0{:s}0{:s}".format(sep, sep, sep, sep))
            fd.write("{:d}{:s}".format(buffer_idx + 1, sep))
            fd.write("{:d}{:s}".format(idx, sep))
            fd.write("\n")

        else:
            # write each coord & id in a new line
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
        iter_images = video_buffer.__iter__()
        for i in range(video_buffer.__len__()):
            image = next(iter_images)

            if self._video is True:
                # Create the sppasVideoWriter() if it wasn't already done.
                # An image is required to properly fix the video size.
                if self._video_writer is None:
                    self._video_writer, fn = self.create_video_writer(out_name, image, "")
                    new_files.append(fn)
                # Write the image, as it
                self._video_writer.write(image)

            if self._img_writer.options.tag is True:

                # Get the list of coords & ids stored for the i-th image
                coords = video_buffer.get_coordinates(i)
                ids = video_buffer.get_ids(i)
                colors = self._get_ids_colors(ids)

                # Create the sppasVideoWriter() if it wasn't already done.
                # An image is required to properly fix the video size.
                if self._tag_video_writer is None:
                    self._tag_video_writer, fn = self.create_video_writer(out_name, image, pattern)
                    new_files.append(fn)

                # Tag&write the image with squares at the coords,
                # and a rectangle with the id
                img = self._img_writer.tag_image(image, coords, colors)
                self._text_image(img, coords, ids, colors)
                self._tag_video_writer.write(img)

        return new_files

    # -----------------------------------------------------------------------

    def _get_ids_colors(self, ids):
        """Return the colors corresponding to the given list of ids."""
        all_colors = self._img_writer.get_colors()
        colors = list()
        for pid in ids:
            if pid not in self.__person_colors:
                # get a new color
                idx = len(self.__person_colors)
                n = len(all_colors['r'])
                # Get the idx-th color
                r = all_colors['r'][idx % n]
                g = all_colors['g'][idx % n]
                b = all_colors['b'][idx % n]
                rgb = (r, g, b)
                self.__person_colors[pid] = rgb
            # append the color for this id
            colors.append(self.__person_colors[pid])

        return colors

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
        ids = video_buffer.get_ids(idx)
        colors = self._get_ids_colors(ids)

        # Draw the coords & ids on a copy of the original image
        img = self._img_writer.tag_image(image, coords)
        self._text_image(img, coords, ids, colors)

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

                # each identifier has its own folder
                id_folder = os.path.join(os.path.dirname(folder), ids[j])
                if os.path.exists(id_folder) is False:
                    os.mkdir(id_folder)

                # Create the image filename, starting by the id
                iname = str(ids[j]) + "_" + img_name + "_" + str(j) + pattern + self._image_ext
                out_iname = os.path.join(id_folder, iname)

                # Crop the given image to the coordinates and
                # resize only if the option width or height is enabled
                img_crop = self._img_writer.crop_and_size_image(image, c)

                # Add the image to the folder
                img_crop.write(out_iname)
                new_files.append(out_iname)

        return new_files
