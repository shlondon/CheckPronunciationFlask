# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.videodata.videobuffer.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Package for the management of video files.

.. _This file is part of SPPAS: <http://www.sppas.org/>
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

import logging

from sppas.src.exceptions import NegativeValueError
from sppas.src.exceptions import IndexRangeException
from sppas.src.exceptions import sppasTypeError
from sppas.src.imgdata import sppasImage

from .video import sppasVideoReader

# ---------------------------------------------------------------------------


class sppasVideoReaderBuffer(sppasVideoReader):
    """Class to manage a video with a buffer (a queue) of images.

    This class allows to use a buffer of images on a video to manage it
    sequentially and to have a better control on it.

    :Example:

    Initialize a VideoBuffer with a size of 100 images and overlap of 10:
    >>> v = sppasVideoReaderBuffer(video, 100, 10)

    Bufferize the next sequence of images of the video:
    >>> v.next()

    Release the flow taken by the reading of the video:
    >>> v.close()

    """

    DEFAULT_BUFFER_SIZE = 100
    DEFAULT_BUFFER_OVERLAP = 0
    MAX_MEMORY_SIZE = 1024*1024*1024   # 1 Gb of RAM

    # -----------------------------------------------------------------------

    def __init__(self, video=None,
                 size=-1,
                 overlap=DEFAULT_BUFFER_OVERLAP):
        """Create a new sppasVideoReaderBuffer instance.

        :param video: (mp4, etc...) The video filename to browse
        :param size: (int) Number of images of the buffer or -1 for auto
        :param overlap: (overlap) The number of images to keep
        from the previous buffer

        """
        super(sppasVideoReaderBuffer, self).__init__()

        # Initialization of the buffer size and buffer overlaps
        self.__nb_img = 0
        self.__overlap = 0
        self.set_buffer_size(size)
        self.set_buffer_overlap(overlap)

        # List of images
        self.__images = list()

        # First and last frame indexes of the buffer
        self.__buffer_idx = (-1, -1)

        # Initialization of the video
        if video is not None:
            self.open(video)
            if size == -1:
                self.set_buffer_size(size)

    # -----------------------------------------------------------------------

    def open(self, video):
        """Override. Create an opencv video capture from the given video.

        :param video: (name of video file, image sequence, url or video
        stream, GStreamer pipeline, IP camera) The video to browse.

        """
        self.reset()
        sppasVideoReader.open(self, video)

    # -----------------------------------------------------------------------

    def close(self):
        """Override. Release the flow taken by the reading of the video."""
        self.reset()
        sppasVideoReader.close(self)

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset the buffer but does not change anything to the video."""
        # List of images
        self.__images = list()

        # Last read frame
        self.__buffer_idx = (-1, -1)

    # -----------------------------------------------------------------------

    def get_buffer_size(self):
        """Return the defined size of the buffer."""
        return self.__nb_img

    # -----------------------------------------------------------------------

    def set_buffer_size(self, value=-1):
        """Set the size of the buffer.

        The new value is applied to the next buffer, it won't affect the
        currently in-use data.
        A value of -1 will fix automatically the buffer to use
        MAX_MEMORY_SIZE Gb of RAM.

        :param value: (int) The new size of the buffer.
        :raise: ValueError

        """
        value = int(value)
        if value == -1:
            if self.is_opened() is False:
                w, h = 1920, 1080
            else:
                w, h = self.get_width(), self.get_height()
            nbytes = w * h * 3  # uint8 for r, g, and b
            value = sppasVideoReaderBuffer.MAX_MEMORY_SIZE // nbytes
            if self.is_opened() is True and value > self.get_nframes():
                value = self.get_nframes()

        if value <= 0:
            raise NegativeValueError(value)

        # The size of the buffer can't be larger than the video size
        if self.is_opened() is True and value > self.get_nframes():
            value = self.get_nframes()
            # raise IntervalRangeException(value, 1, self.get_nframes())

        if self.__overlap >= value:
            raise ValueError("The already defined overlap value {:d} can't be "
                             "greater than the buffer size.")

        self.__nb_img = value
        logging.info("The video buffer is set to {:d} images".format(self.__nb_img))

    # -----------------------------------------------------------------------

    def get_buffer_overlap(self):
        """Return the overlap of the buffer."""
        return self.__overlap

    # -----------------------------------------------------------------------

    def set_buffer_overlap(self, value):
        """Set the number of images to keep from the previous buffer.

        The new value is applied to the next buffer, it won't affect the
        currently in-use data.

        :param value: (int)

        """
        overlap = int(value)
        if overlap >= self.__nb_img or overlap < 0:
            raise ValueError
        self.__overlap = value

    # -----------------------------------------------------------------------

    def seek_buffer(self, value):
        """Set the position of the frame for the next buffer to be read.

        It won't change the current position in the video until "next" is
        invoked. It invalidates the current buffer.

        :param value: (int) Frame position

        """
        value = self.check_frame(value)
        self.reset()
        self.__buffer_idx = (-1, value-1)

    # -----------------------------------------------------------------------

    def tell_buffer(self):
        """Return the frame position for the next buffer to be read.

        Possibly, it can't match the current position in the stream, if
        video.read() was invoked for example.

        """
        return self.__buffer_idx[1] + 1

    # -----------------------------------------------------------------------

    def get_buffer_range(self):
        """Return the indexes of the frames of the current buffer.

        :return: (tuple) start index, end index of the frames in the buffer

        """
        if -1 in self.__buffer_idx:
            return -1, -1
        return self.__buffer_idx

    # -----------------------------------------------------------------------

    def next(self):
        """Fill in the buffer with the next sequence of images of the video.

        :return: False if we reached the end of the video

        """
        if self.is_opened() is False:
            return False

        # Fix the number of frames to read
        nb_frames = self.__nb_img - self.__overlap
        # But if it's the first frame loading, we'll fill in the buffer of the
        # full size, i.e. no overlap is to be applied.
        if self.__buffer_idx[1] == -1:
            nb_frames = self.__nb_img

        # Set the beginning position to read in the video
        start_frame = self.__buffer_idx[1] + 1
        self.seek(start_frame)

        # Launch and store the result of the reading
        result = self.__load_frames(nb_frames)
        next_frame = start_frame + len(result)  #self.tell()

        # Update the buffer and the frame indexes with the current result
        delta = self.__nb_img - self.__overlap
        self.__images = self.__images[delta:]
        self.__buffer_idx = (start_frame - len(self.__images), next_frame - 1)
        self.__images.extend(result)
        result.clear()

        return next_frame != self.get_nframes()

    # -----------------------------------------------------------------------

    def check_buffer_index(self, value):
        """Raise an exception if the given image index is not valid.

        :param value: (int)

        """
        value = int(value)
        if value < 0:
            raise NegativeValueError(value)
        (begin, end) = self.get_buffer_range()
        #if begin == -1 or end == -1:
        #    raise ValueError("Invalid index value: no buffer is loaded.")
        if value < self.get_buffer_size():
            return value
        raise IndexRangeException(value, 0, self.get_buffer_size())

    # -----------------------------------------------------------------------

    def append(self, image):
        """Append an image into the buffer and pop the first if full queue.

        :param image: (sppasImage) A new image to append to the list

        """
        if isinstance(image, sppasImage) is False:
            raise sppasTypeError(type(image), "sppasImage")

        self.__images.append(image)
        if len(self.__images) > self.__nb_img:
            self.__images.pop(0)

    # -----------------------------------------------------------------------

    def pop(self, img_idx):
        """Pop an image of the buffer.

        :param img_idx: (int) Index of the image in the buffer

        """
        img_idx = int(img_idx)
        if 0 < img_idx < self.get_buffer_size():
            self.__images.pop(img_idx)
        else:
            raise IndexRangeException(img_idx, 0, self.get_buffer_size())

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __load_frames(self, nb_frames):
        """Browse a sequence of a video.

        :returns: a list of sppasImage instances

        """
        # fix the exact number of frames to read to stop when the end is reached
        from_pos = self.tell()
        to_pos = self.get_nframes()
        if from_pos + nb_frames > to_pos:
            nb_frames = to_pos - from_pos

        # Create the list to store the images
        images = list()

        # Browse the video
        for i in range(nb_frames):
            # Grab the next frame.
            image_array = self.read_frame()
            # Add the image in the storage list
            images.append(image_array)

        # Return the list of images
        return images

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __len__(self):
        """Return the number of images in the current data buffer."""
        return len(self.__images)

    # -----------------------------------------------------------------------

    def __iter__(self):
        """Browse the current data buffer."""
        for data in self.__images:
            yield data

    # -----------------------------------------------------------------------

    def __getitem__(self, item):
        return self.__images[item]

    # -----------------------------------------------------------------------

    def __str__(self):
        liste = list()
        iterator = self.__iter__()
        for i in range(len(self.__images)):
            liste.append(str(next(iterator)) + "\n")
        return liste

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

