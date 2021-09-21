# -*- coding : UTF-8 -*-
"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech
        http://www.sppas.org/

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

    src.videodata.videoutils.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility functions for videos.

"""

import os
import logging

from sppas.src.wkps.fileutils import sppasDirUtils
from sppas.src.imgdata import image_extensions
from sppas.src.imgdata import sppasImage

from .video import sppasVideoWriter
from .video import sppasVideoReader

# ---------------------------------------------------------------------------


def video_to_images(video, folder, pattern="img_", process_image=True):
    """Create a folder of images from a video.

    :param video: (str) Input video filename.
    :param folder: (str) D=Output directory with images.
    :param process_image: (bool) Apply default options on images (i.e. rotate if in metadata)

    """
    bv = sppasVideoReader()
    bv.open(video)
    nframes = bv.get_nframes()
    ndigits = len(str(nframes))
    ff = str("{:0%dd}" % ndigits)

    frame_idx = 0
    frame = bv.read_frame(process_image)
    while frame is not None:
        # write the image in the folder
        img_name = os.path.join(folder, pattern + ff.format(frame_idx) + ".png")
        frame.write(img_name)

        frame_idx += 1
        frame = bv.read_frame(process_image)
        if frame_idx % 1000 == 0:
            logging.info(" ... {:d} images in folder".format(frame_idx))

    bv.close()

# ---------------------------------------------------------------------------


class sppasImageVideoWriter(sppasVideoWriter):
    """Write a video from a folder with images.

    :author:       Brigitte Bigi
    :contact:      develop@sppas.org

    """

    def __init__(self, folder):
        """Create an instance of sppasImageVideoWriter.

        :param folder: (str) Input directory with images.

        """
        super(sppasImageVideoWriter, self).__init__()

        # number of times we'll write each image, at least 1.
        self.__mul = 1
        # number of times we'll repeat the sequence of images
        self.__repeat = 1

        # list of images in the folder
        logging.debug("Search for images in folder {}".format(folder))
        self.__all_images = list()
        for img_ext in image_extensions:
            img_files = sppasDirUtils.dir_entries(folder, extension=img_ext, subdir=True)
            if len(img_files) > 0:
                logging.debug("... found {} {} images in folder".format(len(img_files), img_ext))
                self.__all_images.extend(img_files)
            else:
                logging.debug(" .. no image found with extension {}".format(img_ext))

    # -----------------------------------------------------------------------

    def img_mul(self, value):
        """Set the number of times to write each image.

        :param value: (int) At least 1.

        """
        value = int(value)
        if value < 1:
            value = 1
        self.__mul = value

    # -----------------------------------------------------------------------

    def repeat(self, value):
        """Set the number of times to repeat the sequence of images.

        :param value: (int) At least 1.

        """
        value = int(value)
        if value < 1:
            value = 1
        self.__repeat = value

    # -----------------------------------------------------------------------

    def export(self, video_name):
        """

        """
        self.open(video_name)

        for r in range(self.__repeat):
            for i, img_name in enumerate(sorted(self.__all_images)):
                img = sppasImage(filename=img_name)
                for x in range(self.__mul):
                    self.write(img)
                if i > 0 and i % 100 == 0:
                    logging.debug("{:d} images added to the video".format(i))

        self.close()

