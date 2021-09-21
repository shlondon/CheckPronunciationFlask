"""
:filename: sppas.src.imgdata.imgsequence.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Create sequence of images with overlays, rotations, ...

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

import logging
import os
import cv2
import numpy

from sppas.src.config import sppasTypeError
from sppas.src.calculus.geometry.linear_fct import slope_intercept
from sppas.src.calculus.geometry.linear_fct import linear_fct

from .image import sppasImage
from .coordinates import sppasCoords

# ---------------------------------------------------------------------------


class ImageSequence(object):
    """Create image sequence.

    """

    def __init__(self, back_image):
        """Create a new instance.

        :param back_image: Either a sppasImage or an ndarray or a filename

        """
        self.__back = self._to_image(back_image)

        # Options to be applied to the over image
        self.do_shadow = False  # add shadow
        self.do_move = False    # mimics of a movement (transparency+blur)
        self.do_rotate = False  # rotate

        # if isinstance(image, list):
        #     self.__img = list()
        #     for img in image:
        #         if isinstance(img, sppasImage) is False:
        #             if isinstance(img, numpy.ndarray):
        #                 img = sppasImage(input_array=img)
        #             else:
        #                 img = sppasImage(filename=img)
        #             self.__img.append(img)

    # -----------------------------------------------------------------------

    @staticmethod
    def _to_image(entry):
        if isinstance(entry, sppasImage) is True:
            return entry

        if isinstance(entry, numpy.ndarray):
            return sppasImage(input_array=entry)

        return sppasImage(filename=entry)

    # -----------------------------------------------------------------------

    def overlays(self, over_image, coord1, coord2, nb_img=0):
        """Over image overlays back image between coords nb times.

        :param over_image: Either a sppasImage or an ndarray or a filename
        :param coord1: (sppasCoords) Position and optionally size to overlay - src
        :param coord2: (sppasCoords) Position and optionally size to overlay - dest
        :param nb_img: (int) Total number of images of the sequence
        :return: (list of sppasImage)

        """
        over = self._to_image(over_image)
        images = list()
        coord1 = sppasCoords.to_coords(coord1)
        coord2 = sppasCoords.to_coords(coord2)
        nb_img = int(nb_img)

        #if self.do_shadow is True:
        #    over = over.ishadow(x, y)

        # Add the image with other pasted at coord1
        images.append(self.__back.ioverlay(over, coord1))

        # Add nb intermediate images
        if nb_img > 2:
            a, b = slope_intercept((coord1.x, coord1.y), (coord2.x, coord2.y))
            step_x = (coord2.x - coord1.x) / float(nb_img + 1)
            step_y = (coord2.y - coord1.y) / float(nb_img + 1)
            step_w = (coord2.w - coord1.w) / float(nb_img)
            step_h = (coord2.h - coord1.h) / float(nb_img)
            prev_c = coord1
            if self.do_move is True:
                blur_other = over.iblur()
                tr_other = blur_other.ialpha(196, direction=-1)
            for i in range(1, nb_img+1):
                pimg = self.__back.copy()
                # coords where to put other in self
                x = max(0, coord1.x + int(step_x * i))
                if coord1.x != coord2.x:
                    y = int(linear_fct(x, a, b))
                else:
                    y = max(0, coord1.y + int(step_y * i))
                w = max(0, coord1.w + int(step_w * i))
                h = max(0, coord1.h + int(step_h * i))
                c = sppasCoords(x, y, w, h)

                # put 3 times other in transparent from prev to cur
                if self.do_move is True and prev_c.x != c.x and prev_c.y != c.y:
                     tr_step_x = (c.x - prev_c.x) // 3
                     tr_step_y = (c.y - prev_c.y) // 3
                     pimg = self.__back.ioverlay(tr_other, (prev_c.x + tr_step_x, prev_c.y + tr_step_y, prev_c.w, prev_c.h))
                     pimg = pimg.ioverlay(tr_other, (prev_c.x + 2*tr_step_x, prev_c.y + 2*tr_step_y, prev_c.w, prev_c.h))
                     pimg = pimg.ioverlay(tr_other, (prev_c.x + 3*tr_step_x, prev_c.y + 3*tr_step_y, prev_c.w, prev_c.h))

                # put other
                pimg = pimg.ioverlay(over, c)
                images.append(pimg)
                prev_c = c

        # Add the image with other pasted at coord2
        images.append(self.__back.ioverlay(over, coord2))

        return images

    # -----------------------------------------------------------------------

    def fade_in(self, nb_img=0, color=(255, 255, 255)):
        """Fade in the image in nb times from the given color.

        :param nb_img: (int) Total number of images of the sequence
        :param color: BGR of the color
        :param alpha: transparency [ignored if the base image has no alpha channel]
        :return: (list of sppasImage)

        """
        images = list()
        img = self.__back.ialpha(value=0, direction=-1)
        w, h = img.size()
        colored_img = sppasImage(0).blank_image(w, h, white=False, alpha=0)
        colored_img = colored_img.iblue(color[0])
        colored_img = colored_img.igreen(color[1])
        colored_img = colored_img.ired(color[2])

        for i in range(nb_img):
            alpha_color = colored_img.ialpha(i * (255//nb_img))
            trimg = img.ioverlay(alpha_color, (0, 0, w, h))
            images.append(trimg)

        return images

