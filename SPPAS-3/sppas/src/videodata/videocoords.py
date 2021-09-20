# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.videodata.videocoords.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  A video buffer with coordinates and video writer stream

.. _This file is part of SPPAS: <http://www.sppas.org/>
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
import shutil
import codecs
import logging

from sppas.src.config import annots
from sppas.src.config import sppasTrash
from sppas.src.exceptions import sppasExtensionWriteError
from sppas.src.exceptions import sppasTypeError
from sppas.src.imgdata import sppasCoords
from sppas.src.imgdata import sppasCoordsImageWriter
from sppas.src.imgdata import image_extensions

from .videobuffer import sppasVideoReaderBuffer
from .video import sppasVideoWriter

video_extensions = tuple(sppasVideoWriter.FOURCC.keys())

# ---------------------------------------------------------------------------


class sppasCoordsVideoBuffer(sppasVideoReaderBuffer):
    """A video buffer of images with a list of coordinates.

    """

    def __init__(self,
                 video=None,
                 size=-1):
        """Create a new instance.

        :param video: (str) The video filename to browse
        :param size: (int) Number of images of the buffer or -1 for auto

        """
        super(sppasCoordsVideoBuffer, self).__init__(video, size=size, overlap=0)

        # The list of list of coordinates
        self.__coords = [list()]*size

    # -----------------------------------------------------------------------

    def reset(self):
        """Override. Reset all the info related to the buffer content."""
        sppasVideoReaderBuffer.reset(self)
        self.__coords = [list()] * self.get_buffer_size()

    # -----------------------------------------------------------------------

    def next(self):
        """Override. Fill in the buffer with the next images & reset coords.

        """
        ret = sppasVideoReaderBuffer.next(self)
        self.__coords = [list()] * self.get_buffer_size()
        return ret

    # -----------------------------------------------------------------------

    def get_coordinates(self, buffer_index=None):
        """Return the coordinates of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :return: (list of sppasCoords) Coordinates

        """
        if buffer_index is not None:
            buffer_index = self.check_buffer_index(buffer_index)
            return self.__coords[buffer_index]
        else:
            if len(self.__coords) != self.__len__():
                raise ValueError("Coordinates were not properly associated to images of the buffer")
            return self.__coords

    # -----------------------------------------------------------------------

    def set_coordinates(self, buffer_index, coords):
        """Set the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coords: (list of sppasCoords) Set the list of coords

        """
        buffer_index = self.check_buffer_index(buffer_index)

        if isinstance(coords, (list, tuple)) is True:
            for c in coords:
                if isinstance(c, sppasCoords) is False:
                    raise sppasTypeError(str(type(c)), "sppasCoords")
            self.__coords[buffer_index] = coords

        else:
            raise TypeError(str(type(coords)), "list/tuple")

    # -----------------------------------------------------------------------

    def index_coordinate(self, buffer_index, coord):
        """Index of the given coordinate."""
        buffer_index = self.check_buffer_index(buffer_index)
        return self.__coords[buffer_index].index(coord)

    # -----------------------------------------------------------------------

    def get_coordinate(self, buffer_index, coord_index):
        """Return a coordinate of a given image.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Index of the coord
        :return: (sppasCoords) Coordinates

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= coord_index < len(self.__coords[buffer_index]):
            return self.__coords[buffer_index][coord_index]

        raise ValueError("Invalid coordinate index value.")

    # -----------------------------------------------------------------------

    def set_coordinate(self, buffer_index, coord_index, coord):
        """Assign the coordinate to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Index of the coord
        :param coord: (sppasCoords) Append the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if 0 <= coord_index < len(self.__coords[buffer_index]):
            if isinstance(coord, sppasCoords):
                self.__coords[buffer_index][coord_index] = coord
            else:
                raise TypeError("")
        else:
            raise ValueError("Invalid coordinate index value.")

    # -----------------------------------------------------------------------

    def append_coordinate(self, buffer_index, coord):
        """Append the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Append the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)

        if isinstance(coord, sppasCoords):
            self.__coords[buffer_index].append(coord)

        else:
            raise TypeError("")

    # -----------------------------------------------------------------------

    def remove_coordinate(self, buffer_index, coord):
        """Remove the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord: (sppasCoords) Remove the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)
        if coord in self.__coords[buffer_index]:
            self.__coords[buffer_index].remove(coord)

    # -----------------------------------------------------------------------

    def pop_coordinate(self, buffer_index, coord_index):
        """Remove the coordinates to a given image index.

        :param buffer_index: (int) Index of the image in the buffer
        :param coord_index: (int) Pop the given coord

        """
        buffer_index = self.check_buffer_index(buffer_index)
        self.__coords[buffer_index].pop(coord_index)

# ---------------------------------------------------------------------------


class sppasCoordsVideoReader(object):
    """Read&create list of coords from a CSV file.

    The CSV file must have the following columns:

        - frame number (ignored)
        - the index of the coords -- int
        - timestamp (ignored)
        - confidence -- float
        - success -- int (0=failed, 1=success)
        - x, y, w, h -- int
        - buffer number (ignored)
        - index in the buffer (ignored)

    """

    def __init__(self, csv_file, separator=";"):
        """Set the list of coords defined in the given file.

        :param csv_file: (str) coords from a sppasCoordsVideoWriter
        :param separator: (char) Columns separator in the CSV file

        """
        self.coords = list()
        prev = -1

        with codecs.open(csv_file, "r") as csv:
            lines = csv.readlines()

        if len(lines) > 0:
            for line in lines:
                columns = line.split(separator)
                # 1st coord = new image
                if int(columns[0]) != prev:
                    self.coords.append(list())
                    prev = int(columns[0])

                if int(columns[4]) == 1 and len(columns) > 8:
                    coord = sppasCoords(int(columns[5]),
                                        int(columns[6]),
                                        int(columns[7]),
                                        int(columns[8]),
                                        float(columns[3]))
                    self.coords[len(self.coords) - 1].append(coord)

# ---------------------------------------------------------------------------


class sppasCoordsVideoWriter(object):
    """Write a video, a set of images and/or coordinates into files.

    There are 3 main solutions to write the result (images+coords):

        1. CSV: coordinates into a spreadsheet
        2. video
        3. folder with images

    For 2 and 3, there are 2 options - at least one has to be selected:

        1. tag: draw a square for each coord in the original image
        2. crop: create one image for each coord

    """

    def __init__(self, image_writer=None):
        """Create a new instance.

        Parts of each image can be extracted in separate image files and/or
        surrounded on the given image.
        Output video and images can be resized.

        """
        # Manage options and write images if needed
        self._img_writer = sppasCoordsImageWriter()
        if image_writer is not None:
            if isinstance(image_writer, sppasCoordsImageWriter) is True:
                self._img_writer = image_writer

        # sppasVideoWriter() for the ouput videos - if tag/video options.
        self._video_writer = None
        self._tag_video_writer = None

        # Added options compared to the image writer
        self._video = False   # save the images of the buffer in a video
        self._folder = False  # save results as images in a folder
        self._fps = 25.       # default video framerate -- important

        # The default output file extensions
        self._video_ext = annots.video_extension
        self._image_ext = annots.image_extension

    # -----------------------------------------------------------------------
    # Getters and setters for the options
    # -----------------------------------------------------------------------

    def get_video_extension(self):
        """Return the extension for video files."""
        return self._video_ext

    # -----------------------------------------------------------------------

    def set_video_extension(self, ext):
        """Set the extension of video files."""
        ext = str(ext)
        if ext.startswith(".") is False:
            ext = "." + ext
        if ext not in video_extensions:
            raise sppasExtensionWriteError(ext)

        self._video_ext = ext

    # -----------------------------------------------------------------------

    def get_image_extension(self):
        """Return the extension for image files."""
        return self._image_ext

    # -----------------------------------------------------------------------

    def set_image_extension(self, ext):
        """Set the extension of image files."""
        ext = str(ext)
        if ext.startswith(".") is False:
            ext = "." + ext
        if ext not in image_extensions:
            raise sppasExtensionWriteError(ext)

        self._image_ext = ext

    # -----------------------------------------------------------------------

    def get_fps(self):
        """Return the defined fps value to write video files (float)."""
        return self._fps

    # -----------------------------------------------------------------------

    def set_fps(self, value):
        """Fix the framerate of the output video.

        :param value: (float) Number of frames per seconds
        :raise: NegativeValueError, IntervalRangeError

        """
        # if the value isn't correct, sppasVideoWriter() will raise an exc.
        w = sppasVideoWriter()
        w.set_fps(value)
        self._fps = value

    # -----------------------------------------------------------------------

    def get_video_output(self):
        """Return True if images will be saved into a video, as it."""
        return self._video

    # -----------------------------------------------------------------------

    def get_csv_output(self):
        """Return True if coordinates will be saved in a CSV file."""
        return self._img_writer.options.get_csv_output()

    # -----------------------------------------------------------------------

    def get_folder_output(self):
        """Return True if results will be saved in a folder of image files."""
        return self._folder

    # -----------------------------------------------------------------------

    def get_tag_output(self):
        """Return True if faces of the images will be surrounded."""
        return self._img_writer.options.get_tag_output()

    # -----------------------------------------------------------------------

    def get_crop_output(self):
        """Return True if the option to crop faces is enabled."""
        return self._img_writer.options.get_crop_output()

    # -----------------------------------------------------------------------

    def get_output_width(self):
        """Return the width of the output image files."""
        return self._img_writer.options.get_width()

    # -----------------------------------------------------------------------

    def get_output_height(self):
        """Return the height of the outputs files."""
        return self._img_writer.options.get_height()

    # -----------------------------------------------------------------------

    def set_options(self, csv=None, tag=None, crop=None,
                    width=None, height=None, folder=None):
        """Set any/some/all of the options."""
        self._img_writer.set_options(csv, tag, crop, width, height)
        if folder is not None:
            self._folder = bool(folder)

    # -----------------------------------------------------------------------

    def set_video_output(self, value):
        """Set true to enable the output of the video, as it."""
        self._video = bool(value)

    # -----------------------------------------------------------------------
    # Write into CSV, VIDEO or IMAGES
    # -----------------------------------------------------------------------

    def get_image_size(self, image):
        """Return the size of the image depending on the image and options."""
        return image.get_proportional_size(
            width=self._img_writer.options.get_width(),
            height=self._img_writer.options.get_height()
        )

    # -----------------------------------------------------------------------

    def close(self):
        """Close all currently used sppasVideoWriter().

        It has to be invoked when writing buffers is finished in order to
        release the video writers.

        """
        if self._tag_video_writer is not None:
            self._tag_video_writer.close()
            self._tag_video_writer = None

    # -----------------------------------------------------------------------

    def write(self, video_buffer, out_name, opt_pattern=""):
        """Save the result into file(s) depending on the options.

        The out_name is a base name, its extension is ignored and replaced by
        the one(s) defined in this class.

        :param video_buffer: (sppasCoordsVideoBuffer) The images and results to write
        :param out_name: (str) The output name for the folder and/or the video
        :param opt_pattern: (str) Optional pattern to add to filename(s)
        :return: list of newly created file names

        """
        new_files = list()

        # Remove any existing extension, and ignore it!
        fn, _ = os.path.splitext(out_name)
        out_name = fn

        # Write results in CSV format
        if self._img_writer.options.csv is True:
            out_csv_name = out_name + opt_pattern + ".csv"
            self.write_csv_coords(video_buffer, out_csv_name)
            new_files.append(out_csv_name)

        # Write results in VIDEO format
        if self.get_video_output() is True or self._img_writer.options.get_tag_output() is True:
            new_video_files = self.write_video(video_buffer, out_name, opt_pattern)
            if len(new_video_files) > 1:
                logging.info("{:d} video files created".format(len(new_video_files)))
            new_files.extend(new_video_files)

        # Write results in IMAGE format
        if self._folder is True:
            new_image_files = self.write_folder(video_buffer, out_name, opt_pattern)
            if len(new_image_files) > 1:
                logging.info("{:d} image files created".format(len(new_image_files)))
            # Too many files are created, they can't be added to the GUI...
            # TODO: Find a solution in the GUI to deal with a huge nb of files
            # then un-comment the next line
            # new_files.extend(new_image_files)

        return new_files

    # -----------------------------------------------------------------------

    def write_csv_coords(self, video_buffer, out_csv_name):
        """Write or append a list of coordinates in a CSV file.

        :param video_buffer: (sppasFacesVideoBuffer) The images and results to write
        :param out_csv_name: (str) The filename of the CSV file to write

        """
        # Get information about the buffer
        begin_idx, end_idx = video_buffer.get_buffer_range()
        buffer_nb = end_idx // video_buffer.get_buffer_size()

        # Open or re-open the CSV file to append the new results
        mode = "w"
        if os.path.exists(out_csv_name) is True:
            # if it's the first buffer, the file should not exist
            if buffer_nb == 0:
                trash_name = sppasTrash().put_file_into(out_csv_name)
                logging.warning("A file with name {:s} is already existing.\n"
                                "This file is moved into the Trash of SPPAS "
                                "with name: {:s}".format(out_csv_name, trash_name))
            else:
                mode = "a+"

        with codecs.open(out_csv_name, mode, encoding="utf-8") as fd:
            for i in range(video_buffer.__len__()):
                self.write_coords(fd, video_buffer, buffer_nb, i)

    # -----------------------------------------------------------------------

    def write_coords(self, fd, video_buffer, buffer_idx, idx):
        """Write the coords into the given stream.

        - frame number
        - the index of the coords
        - timestamp
        - confidence
        - success
        - x, y, w, h,
        - buffer number
        - index in the buffer

        :param fd: (Stream) File descriptor, String descriptor, stdout, etc
        :param video_buffer: (sppasCoordsVideoBuffer)
        :param buffer_idx: (int) Buffer number
        :param idx: (int) An integer to write

        """
        sep = self._img_writer.get_csv_sep()

        # Get the list of coordinates stored for the i-th image
        coords = video_buffer.get_coordinates(idx)
        frame_idx = (buffer_idx * video_buffer.get_buffer_size()) + idx

        # Write the coords
        if len(coords) == 0:
            # no coords for the given image
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
            # write each coords in a new line
            for j in range(len(coords)):
                fd.write("{:d}{:s}".format(frame_idx + 1, sep))
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
        if pattern == "" and self._video is True and self._img_writer.options.tag is True:
            pattern = "-tag"

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
                # Get the list of coordinates stored for the i-th image
                coords = video_buffer.get_coordinates(i)

                # Create the sppasVideoWriter() if it wasn't already done.
                # An image is required to properly fix the video size.
                if self._tag_video_writer is None:
                    self._tag_video_writer, fn = self.create_video_writer(out_name, image, pattern)
                    new_files.append(fn)

                # Tag&write the image with squares at the coords
                img = self._img_writer.tag_image(image, coords)
                self._tag_video_writer.write(img)

        return new_files

    # -----------------------------------------------------------------------

    def write_folder(self, video_buffer, out_name, pattern=""):
        """Save the result in image format into a folder.

        :param video_buffer: (sppasImage) The image to write
        :param out_name: (str) The folder name of the output image files
        :param pattern: (str) Pattern to add to a cropped image filename

        """
        new_files = list()
        # Create the directory with all results
        if os.path.exists(out_name) is False:
            os.mkdir(out_name)

        # Create a folder to save results of this buffer
        begin_idx, end_idx = video_buffer.get_buffer_range()
        folder = os.path.join(out_name, "{:06d}".format(begin_idx))
        if os.path.exists(folder) is True:
            shutil.rmtree(folder)
        os.mkdir(folder)

        iter_images = video_buffer.__iter__()
        for i in range(video_buffer.__len__()):
            image = next(iter_images)
            img_name = self.__image_name(begin_idx + i)

            nf = self._tag_and_crop(video_buffer, image, i, img_name, folder, pattern)
            new_files.extend(nf)

        return new_files

    # -----------------------------------------------------------------------

    def _tag_and_crop(self, video_buffer, image, idx, img_name, folder, pattern):

        new_files = list()
        # Get the list of coordinates stored for the i-th image
        coords = video_buffer.get_coordinates(idx)

        # Tag and write the image
        if self._img_writer.options.tag is True:
            # Tag&Save the image
            img = self._img_writer.tag_image(image, coords)
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
                img = self._img_writer.crop_and_size_image(image, coords[j])

                # Add the image to the folder
                img.write(out_iname)
                new_files.append(out_iname)

        return new_files

    # -----------------------------------------------------------------------

    def create_video_writer(self, out_name, image, pattern=""):
        """Create a sppasVideoWriter()."""
        # Fix width and height of the video
        w, h = self.get_image_size(image)

        # Fix the video filename
        filename = "{:s}{:s}".format(out_name, pattern) + self._video_ext
        logging.debug("Create a video writer {:s}. Size {:d}, {:d}"
                      "".format(filename, w, h))

        if os.path.exists(filename) is True:
            trash_filename = sppasTrash().put_file_into(filename)
            logging.warning("A file with name {:s} is already existing.\n"
                            "This file is moved into the Trash of SPPAS "
                            "with name: {:s}".format(filename, trash_filename))

        # Create a writer
        try:
            writer = sppasVideoWriter()
            writer.set_size(w, h)
            writer.set_fps(self._fps)
            writer.set_aspect("extend")
            writer.open(filename)
        except Exception as e:
            logging.error("OpenCV failed to open the VideoWriter for file "
                          "{}: {}".format(filename, str(e)))
            return None

        return writer, filename

    # -----------------------------------------------------------------------

    @staticmethod
    def __image_name(idx):
        """Return an image name from its index."""
        return "img_{:06d}".format(idx)

