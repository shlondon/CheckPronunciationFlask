"""
:filename: sppas.src.imgdata.image.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Image data structure.

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

from sppas.src.config import sppasIOError
from sppas.src.config import sppasTypeError
from sppas.src.config import NegativeValueError
from sppas.src.calculus.geometry.linear_fct import slope_intercept
from sppas.src.calculus.geometry.linear_fct import linear_fct

from .coordinates import sppasCoords
from .imgdataexc import ImageReadError
from .imgdataexc import ImageWriteError

# ----------------------------------------------------------------------------


class sppasImage(numpy.ndarray):
    """Manipulate images represented by an ndarray of BGR colors.

    :Example:
        >>> # explicit constructor to create an image
        >>> img1 = sppasImage(shape=(3,))
        >>> # read the image from a file
        >>> img2 = sppasImage(filename=os.path.join("some image file"))
        >>> # construct from an existing ndarray
        >>> img3 = sppasImage(input_array=img1)
        >>> # construct a blank image
        >>> black = sppasImage(0).blank(w=100, h=100, white=False)

    An image of width=320 and height=200 is represented by len(img)=200;
    each of these 200 rows contains 320 lists of [b,g,r] values.

    Important:
    When the image file is read with the OpenCV function imread(),
    the order of colors is BGR (blue, green, red), and the same with
    imwrite. This class is then using BGR colors in an ndarray.

    It ignores alpha values even if specified in the original image.

    """

    def __new__(cls, shape=0, dtype=numpy.uint8, buffer=None, offset=0,
                strides=None, order=None, input_array=None, filename=None):
        """Return the instance of this class.

        Image is created either with the given input array, or with the
        given filename or with the given shape in order of priority.

        :param shape: (int)
        :param dtype: (type)
        :param buffer: (any)
        :param offset: (int)
        :param strides:
        :param order:
        :param input_array: (numpy.ndarray) Array representing an image
        :param filename: (str) Name of a file to read the image
        :raise: IOError

        :Example:
            >>> img1 = sppasImage(shape=(3,), input_array=img, filename="name")
            >>> assert(img1 == img)
            >>> # get image size
            >>> w, h = img1.size()
            >>> # Assigning colors to each pixel
            >>> for i in range(h):
            >>>     for j in range(w):
            >>>         img1[i, j] = [i%256, j%256, (i+j)%256]

        """
        # Priority is given to the given already created array
        if input_array is not None:
            if isinstance(input_array, numpy.ndarray) is False:
                raise sppasTypeError(input_array, "sppasImage, numpy.ndarray")

        else:
            if filename is not None:
                if os.path.exists(filename) is False:
                    raise sppasIOError(filename)

                # imread() decodes the image into a matrix with the color channels
                # stored in the order of Blue, Green, Red and optionally A (Transparency) respectively.
                input_array = cv2.imread(filename, flags=cv2.IMREAD_UNCHANGED)
                if input_array is None:
                    raise ImageReadError(filename)
            else:
                # Create the ndarray instance of our type, given the usual
                # ndarray input arguments. This will call the standard
                # ndarray constructor, but return an object of our type.
                input_array = numpy.ndarray.__new__(cls, shape, dtype, buffer, offset, strides, order)

        # Finally, we must return the newly created object.
        # Return a view of it in order to set it to the right type.
        frame = input_array.view(sppasImage)
        if len(frame.shape) == 2:
            return sppasImage(input_array=cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR))
        return frame

    # -----------------------------------------------------------------------

    @property
    def width(self):
        w = self.shape[1]
        return w

    # -----------------------------------------------------------------------

    @property
    def height(self):
        h = self.shape[0]
        return h

    # -----------------------------------------------------------------------

    @property
    def channel(self):
        if len(self.shape) > 2:
            _, _, c = self.shape
        else:
            c = 0
        return c

    # -----------------------------------------------------------------------
    
    @property
    def center(self):
        """Return the position (x, y) of the center of the image."""
        (w, h) = self.size()
        return w // 2, h // 2

    # -----------------------------------------------------------------------

    def size(self):
        # grab the dimensions of the image
        (h, w) = self.shape[:2]
        return w, h

    # -----------------------------------------------------------------------

    def euclidian_distance(self, other):
        """Return the euclidian distance with the image.

        :param other: (sppasImage) an image with the same shape

        """
        w, h = self.size()
        d = numpy.linalg.norm(self - other, axis=1)
        return sum(sum(d)) / (w * h * 3)

    # -----------------------------------------------------------------------

    def blank_image(self, w=0, h=0, white=False, alpha=None):
        """Create and return an image with black pixels only.

        :param w: (int) Image width. 0 means to use the current image width.
        :param h: (int) Image height. 0 means to use the current height.
        :param white: (bool) Return a white image instead of a black one.
        :param alpha: (int) Add alpha channel with the given int value
        :return: (sppasImage) Fully black BGR image

        """
        if w < 0:
            raise NegativeValueError(w)
        if h < 0:
            raise NegativeValueError(h)
        if w == 0:
            w = self.width
        if h == 0:
            h = self.height

        # Creation of array
        t = (h, w, 3)
        nparray = numpy.zeros(t, dtype=numpy.uint8)
        if white is True:
            nparray = nparray[:, :, (0, 1, 2)] + 255

        img = sppasImage(input_array=nparray)
        if alpha is not None:
            return img.ialpha(alpha)

        return img

    # -----------------------------------------------------------------------
    # Modify colors
    # -----------------------------------------------------------------------

    def ired(self, value=0):
        """Return a copy of the image in red-color.
        
        :param value: (int) Fixed red value ranging (0, 255)
        :return: (sppasImage)
        
        """
        value = int(value)
        value = value % 255
        img = self.copy()
        img[:, :, (0, 1)] = value
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------
    
    def igreen(self, value=0):
        """Return a copy of the image in green-color.
        
        :param value: (int) Fixed green value ranging (0, 255)
        :return: (sppasImage)
        
        """
        value = int(value)
        value = value % 255
        img_green = self.copy()
        img_green[:, :, (0, 2)] = value
        return sppasImage(input_array=img_green)

    # -----------------------------------------------------------------------

    def iblue(self, value=0):
        """Return a copy of the image in blue-color.
        
        :param value: (int) Fixed blue value ranging (0, 255)
        :return: (sppasImage)
        
        """
        value = int(value)
        value = value % 255
        img = self.copy()
        img[:, :, (1, 2)] = value
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------

    def ialpha(self, value=0, direction=0):
        """Return an (numpy.ndarray) representing the image in RGBA colors.

        Do nothing if no channel defined.

        :param value: (int) Alpha value for transparency (0-255)
        :param direction: (int) 0 means to assign the value to each pixel, but
        -1 means to only assign the value to pixels if the existing transparency
        is higher than value (lowers are un-changed) and +1 means to assign
        alpha value if the existing one is lower (higher values are unchanged).

        """
        if self.channel == 3:
            imga = sppasImage(input_array=cv2.cvtColor(self, cv2.COLOR_RGB2RGBA))
        else:
            imga = self.copy()

        if imga.channel == 4:
            value = int(value)
            value = value % 255
            if direction == 0:
                imga[:, :, 3] = value
            elif direction < 0:
                numpy.clip(imga[:, :, 3], 0, value, out=imga[:, :, 3])
            else:
                numpy.clip(imga[:, :, 3], value, 255, out=imga[:, :, 3])

        return imga

    # -----------------------------------------------------------------------

    def ibgr(self, bgr):
        """Return the image with given in BGR or BGRA color values.

        """
        if len(bgr) < 3:
            raise ValueError("Expected a (b, g, r) or (b, g, r, a) color. Got {} instead.".format(bgr))
        img = self.copy()
        # Blue
        value = int(bgr[0])
        value = value % 255
        img[:, :, 0] = value
        # Green
        value = int(bgr[1])
        value = value % 255
        img[:, :, 1] = value
        # Red
        value = int(bgr[2])
        value = value % 255
        img[:, :, 2] = value
        # Alpha
        if len(bgr) == 4:
            return img.ialpha(bgr[3])

        return img

    # -----------------------------------------------------------------------

    def igray(self):
        """Return a copy of the image in grayscale."""
        # The formula is Y' = 0.2989 R + 0.5870 G + 0.1140 B
        # Reminder: our image is BGR or BGRA
        if self.channel == 4:
            avg = numpy.average(self, weights=[0.114, 0.587, 0.2989, 1], axis=2)
        elif self.channel == 3:
            avg = numpy.average(self, weights=[0.114, 0.587, 0.2989], axis=2)
        else:
            return self.copy()

        gray = self.copy()
        gray[:, :, 0] = avg
        gray[:, :, 1] = avg
        gray[:, :, 2] = avg

        return sppasImage(input_array=gray)

    # -----------------------------------------------------------------------

    def inegative(self):
        """Return a negative/positive color image."""
        img = 255 - self
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------

    def ireduction(self, value=128):
        """Apply a color-reduction.

        :param value: (int) Reduction value in range(0, 255)
        :return: (sppasImage)

        """
        value = int(value)
        if value < 0:
            return self.copy()
        coeff = value % 255
        img = self // coeff * coeff
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------

    def igamma(self, coeff=1.0):
        """Return a copy of the image with lightness changed.

        :param coeff: (float) Set a value inn range (0., 1.) to increase
        lightness and a value > 1. to increase darkness.
        :return: (sppasImage)

        """
        if coeff < 0.:
            coeff = 0.
        img = 255.0 * (self / 255.0) ** coeff
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------

    def ito_rgb(self):
        """Return an (numpy.ndarray) representing the image in RGB/RGBA colors.

        """
        img = self.copy()
        if self.channel == 3:
            return img[:, :, [2, 1, 0]]
        elif self.channel == 4:
            return img[:, :, [2, 1, 0, 3]]

        raise sppasTypeError("image", "BGR/BGRA sppasImage")

    # -----------------------------------------------------------------------

    def ishadow(self, x, y):
        tmp = self.igray()
        tmp = tmp.ishift(5, 20)
        return tmp.ioverlay(self, (0, 0))

    # -----------------------------------------------------------------------
    # Modify size
    # -----------------------------------------------------------------------

    def icrop(self, coord):
        """Return a trimmed part of the image to given coordinates.

        :param coord: (sppasCoords) crop to these x, y, w, h values.
        :return: (sppasImage)

        """
        coord = sppasCoords.to_coords(coord)
        x1 = coord.x
        x2 = coord.x + coord.w
        y1 = coord.y
        y2 = coord.y + coord.h
        cropped = self[y1:y2, x1:x2]

        return sppasImage(input_array=cropped)

    # ------------------------------------------------------------------------

    def itrim(self, coord):
        return self.icrop(coord)

    # ------------------------------------------------------------------------

    def iresize(self, width=0, height=0):
        """Return a new array with the specified width and height.

        :param width: (int) The width to resize to (0=proportional to height)
        :param height: (int) The height to resize to (0=proportional to width)
        :return: (sppasImage)

        """
        prop_width, prop_height = self.get_proportional_size(width, height)
        if prop_width+prop_height == 0:
            return self.copy()

        # Choose the interpolation method
        dif = self.height if self.height > self.width else self.width
        interpol = cv2.INTER_AREA if dif > (width + height) // 2 else cv2.INTER_CUBIC

        image = cv2.resize(self, (prop_width, prop_height), interpolation=interpol)

        return sppasImage(input_array=image)

    # ------------------------------------------------------------------------

    def izoom(self, width, height):
        """Resize and crop the image to zoom it to the given size.

        Keep the original aspect ratio of the image, crop if necessary.

        :param width: (int) The width to resize to
        :param height: (int) The height to resize to
        :return: (sppasImage)

        """
        aspect_ratio = int(100. * float(self.width) / float(self.height)) / 100.
        res_aspect_ratio = int(100. * float(width) / float(height)) / 100.

        if aspect_ratio > res_aspect_ratio:
            img_w = int(aspect_ratio * float(height))
            img_h = height
            img = self.iresize(img_w, img_h)
            x1 = int((float(img_w - width)) / 2.)
            x2 = x1 + width
            img = img[:, x1:x2, :]

        elif aspect_ratio < res_aspect_ratio:
            img_w = width
            img_h = int(float(width) / aspect_ratio)
            img = self.iresize(img_w, img_h)
            y1 = int(float(img_h - height) / 2.)
            y2 = y1 + height
            img = img[y1:y2, :, :]

        else:
            # aspect_ratio == res_aspect_ratio:
            img = self.iresize(width, height)

        return sppasImage(input_array=img)

    # ------------------------------------------------------------------------

    def icenter(self, width, height):
        """Center the image into a blank image of the given size.

        Keep the original aspect ratio of the image, crop if necessary or
        add a black border all around.

        :param width: (int) The width to resize to
        :param height: (int) The height to resize to
        :return: (sppasImage)

        """
        # Crop the image if the expected width/height are smaller
        coord = sppasCoords(0, 0, width, height)
        if self.width > width:
            # the image width must be cropped
            coord.x = (self.width - width) // 2
        if self.height > height:
            # the image width must be cropped
            coord.y = (self.height - height) // 2
        img = self.icrop(coord)

        # Create a blank image of the expected width and height
        mask = self.blank_image(width, height)

        # Fix the position of the image into the mask
        x_pos = (width - img.width) // 2
        y_pos = (height - img.height) // 2

        # Replace (BGR) values of the mask by the ones of the image
        mask[y_pos:y_pos + img.height, x_pos:x_pos + img.width, :] = img[:img.height, :img.width, :]

        return sppasImage(input_array=mask)

    # ------------------------------------------------------------------------

    def iextend(self, width, height):
        """Scale the image to match the given size, keeping aspect ratio.

        Keep the original aspect ratio of the image, add a black border.

        :param width: (int) The width to resize to
        :param height: (int) The height to resize to
        :return: (sppasImage)

        """
        aspect_ratio = int(100. * float(self.width) / float(self.height)) / 100.
        res_aspect_ratio = int(100. * float(width) / float(height)) / 100.

        if aspect_ratio == res_aspect_ratio:
            return self.iresize(width, height)

        if aspect_ratio > res_aspect_ratio:
            coeff = float(width) / float(self.width)
            img = self.iresize(width, int(coeff * float(self.height)))

        else:
            coeff = float(height) / float(self.height)
            img = self.iresize(int(coeff * float(self.width)), height)

        # Add a black border where it's missing
        return img.icenter(width, height)

    # ------------------------------------------------------------------------

    def irotate(self, angle, center=None, scale=1.0):
        """Return a new array with the image rotated to the given angle.

        This method is part of imutils under the terms of the MIT License (MIT)
        Copyright (c) 2015-2016 Adrian Rosebrock, http://www.pyimagesearch.com
        See here for details:
        https://www.pyimagesearch.com/2017/01/02/rotate-images-correctly-with-opencv-and-python/

        :param angle: (float) Rotation angle in degrees.
        :param center: (int) Center of the rotation in the source image.
        :param scale: (float) Isotropic scale factor.
        :return: (sppasImage)

        """
        # grab the dimensions of the image and then determine the center
        (h, w) = self.shape[:2]
        if center is None:
            center = (w // 2, h // 2)

        # grab the rotation matrix (applying the negative of the
        # angle to rotate clockwise), then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        matrix = cv2.getRotationMatrix2D(center, -angle, scale)
        cos = numpy.abs(matrix[0, 0])
        sin = numpy.abs(matrix[0, 1])
        # compute the new bounding dimensions of the image
        new_width = int((h * sin) + (w * cos))
        new_height = int((h * cos) + (w * sin))
        # adjust the rotation matrix to take into account translation
        matrix[0, 2] += (new_width // 2) - center[0]
        matrix[1, 2] += (new_height // 2) - center[1]
        # perform the actual rotation and return the image
        rotated = cv2.warpAffine(self, matrix, (new_width, new_height))
        return sppasImage(input_array=rotated)

    # ------------------------------------------------------------------------
    # move content
    # ------------------------------------------------------------------------

    def ishift(self, x, y):
        """Shift the content at left/right and top/bottom.

        """
        # grab the dimensions of the image
        (h, w) = self.shape[:2]

        # create a translation matrix
        matrix = numpy.float32([
            [1, 0, x],
            [0, 1, y]
        ])
        shifted = cv2.warpAffine(self, matrix, (w, h))
        return sppasImage(input_array=shifted)

    # ------------------------------------------------------------------------

    def iflip(self, flip_code=-1):
        """Return a flipped copy of the image.

        flip_code = 0: flip vertically
        flip_code > 0: flip horizontally
        flip_code < 0: flip vertically and horizontally

        :param flip_code: (int) Indicate the way to flip the image

        """
        if flip_code == 0:
            # Flip up-down
            img = numpy.flipud(self)
        elif flip_code > 0:
            # Flip left-right
            img = numpy.fliplr(self)
        else:
            img = numpy.flip(self, (0, 1))

        # flipped = cv2.flip(self, flip_code)
        return sppasImage(input_array=img)

    # -----------------------------------------------------------------------

    def imask(self, other):
        """Return the image masked with the other image.

        :param other: (sppasImage) Image to mask (black areas)
        :param coord: (sppasCoords) Area to mask self with other

        """
        w, h = self.size()
        other = other.iresize(w, h)
        dst = self * other / 255
        dst.astype(numpy.uint8)
        return sppasImage(input_array=dst)

    # -----------------------------------------------------------------------

    def iblur(self):
        """Return the image with smoothed borders."""
        mask_blur = cv2.GaussianBlur(self, (51, 51), 0)
        return sppasImage(input_array=mask_blur)

    # -----------------------------------------------------------------------

    def icontours(self, threshold=128, color=(0, 255, 0)):
        """Return a blank image with the contours of the image in color.

        :param threshold: (int) value which is used to classify the pixel values (0-255)
        :param color: (tuple) BGR values of the color to draw the contours

        """
        # convert image to grey
        img_grey = cv2.cvtColor(self, cv2.COLOR_BGR2GRAY)

        # get threshold image
        ret, thresh_img = cv2.threshold(img_grey, threshold, 255, cv2.THRESH_BINARY)

        # find contours
        contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # create an empty image for contours
        img_contours = numpy.zeros(self.shape)
        # draw the contours on the empty image
        cv2.drawContours(img_contours, contours, -1, color, 3)

        return sppasImage(input_array=img_contours)

    # ------------------------------------------------------------------------

    def get_proportional_size(self, width=0, height=0):
        """Return the size of the image or a proportional size.

        :param width: (int) Force the image to the width
        :param height: (int) Force the image to the height
        :return: (int, int) Width and height

        """
        if len(self) == 0:
            return 0, 0
        width = sppasCoords.to_dtype(width)
        height = sppasCoords.to_dtype(height)
        if width < 0:
            raise NegativeValueError(width)
        if height < 0:
            raise NegativeValueError(height)

        (h, w) = self.shape[:2]
        if width+height == 0:
            return w, h

        prop_width = prop_height = 0
        propw = proph = 1.
        if width != 0:
            prop_width = width
            propw = float(width) / float(w)
        if height != 0:
            prop_height = height
            proph = float(height) / float(h)
        if width == 0:
            prop_width = int(float(w) * proph)
        if height == 0:
            prop_height = int(float(h) * propw)

        return prop_width, prop_height

    # -----------------------------------------------------------------------
    # Tag the image at coords
    # -----------------------------------------------------------------------

    def ipaste(self, other, coord):
        """Replace the current image with the given one at given coords.

        :param other: (sppasImage) Image to paste
        :param coord: (sppasCoords) Position and optionally size to paste
        :return: (sppasImage)

        """
        img = self.copy()
        other = sppasImage(input_array=other)
        coord = sppasCoords.to_coords(coord)

        if other.channel != self.channel:
            if other.channel == 3 and self.channel == 4:
                # Add alpha channel to other
                other = other.ialpha(0)
            if other.channel == 4 and self.channel == 3:
                # Add alpha channel to the self-copied image
                img = self.ialpha(0)

        # Create the image to paste -- resize
        if coord.w > 0 and coord.h > 0:
            paste_img = other.iresize(coord.w, coord.h)
        else:
            paste_img = other
            w, h = other.size()
            coord.w = w
            coord.h = h

        # Create the image to paste -- crop
        w, h = self.size()
        if coord.x + coord.w > w:
            new_w = w - coord.x
            paste_img = paste_img.icrop((0, 0, new_w, coord.h))
        if coord.y + coord.h > h:
            new_h = h - coord.y
            paste_img = paste_img.icrop((0, 0, coord.w, new_h))

        # Paste into a copied image
        x1 = coord.x
        x2 = coord.x + coord.w
        y1 = coord.y
        y2 = coord.y + coord.h
        img[y1:y2, x1:x2] = paste_img

        return img

    # -----------------------------------------------------------------------

    def iblend(self, other, coord=None, weight1=0.5, weight2=0.5):
        """Return the image with the other image added or blended.

        :param other: (sppasImage) Image to blend with
        :param coord: (sppasCoord) Blend only the given area of self with other
        :param weight1: (float) coeff on the image
        :param weight2: (float) coeff on the other image
        :return: (sppasImage)

        """
        w, h = self.size()
        img = self.copy()

        if coord is None:
            other = other.iresize(w, h)
        else:
            blank = sppasImage(0).blank_image(w, h, white=False, alpha=0)
            if other.channel == 3:
                other = other.ialpha(254)
            other = blank.ipaste(other, coord)
            if self.channel == 3:
                img = self.ialpha(254)

        blended = cv2.addWeighted(img, weight1, other, weight2, 0)
        return sppasImage(input_array=blended)

    # -----------------------------------------------------------------------

    def ioverlay(self, other, coord):
        """Return the image with the other image added.

        :param other: (sppasImage) Image to blend with
        :param coord: (sppasCoord) Overlay in the given area of self with other
        :return: (sppasImage)

        """
        back_image = self.copy()
        w, h = self.size()
        over_image = sppasImage(input_array=other)
        coord = sppasCoords.to_coords(coord)

        if over_image.channel == 3:
            # Add alpha channel to other
            over_image = over_image.ialpha(254)
        if back_image.channel == 3:
            # Add alpha channel to the self-copied image
            back_image = self.ialpha(254)

        # Resize the over image to the appropriate size
        if coord.w > 0 and coord.h > 0:
            over_image = over_image.iresize(coord.w, coord.h)
        cols, rows = over_image.shape[:2]
        x = coord.x
        y = coord.y
        # Change the values if the other image goes out of the back image
        if x + rows > w:
            rows = w - x
        if y + cols > h:
            cols = h - y

        # create an over image with the same size of the back one
        tmp = sppasImage(0).blank_image(w, h, white=False, alpha=254)
        over_image = tmp.ipaste(over_image, (x, y))

        # normalize alpha channels from 0-255 to 0-1
        alpha_background = back_image[:, :, 3] / 255.0
        alpha_foreground = over_image[:, :, 3] / 255.0

        # set adjusted colors
        roi_over = back_image.copy()
        for color in range(0, 3):
            roi_over[:, :, color] = alpha_foreground * over_image[:, :, color] + \
                               alpha_background * roi_over[:, :, color] * (1 - alpha_foreground)

        # set adjusted alpha and denormalize back to 0-255
        roi_over[:, :, 3] = (1 - (1 - alpha_foreground) * (1 - alpha_background)) * 255

        # make the ROI in black into the background
        black = sppasImage(0).blank_image(rows, cols, white=False, alpha=254)
        back_image = back_image.ipaste(black, (x, y))

        combined = cv2.add(back_image, roi_over)
        return sppasImage(input_array=combined)

    # -----------------------------------------------------------------------

    def isurround(self, coords, color=(50, 100, 200), thickness=2, score=False):
        """Return a new image with a square surrounding all the given coords.

        :param coords: (List of sppasCoords) Areas to surround
        :param color: (int, int, int) Rectangle color
        :param thickness: (int) Thickness of lines that make up the rectangle. Negative values, like CV_FILLED , mean that the function has to draw a filled rectangle.
        :param score: (bool) Add the confidence score of the coords
        :return: (sppasImage)

        """
        img = self.copy()
        for c in coords:
            c = sppasCoords.to_coords(c)
            if c.w > 0 and c.h > 0:
                # Draw the square and eventually the confidence inside the square
                text = ""
                if score is True and c.get_confidence() > 0.:
                    text = "{:.3f}".format(c.get_confidence())
                img.surround_coord(c, color, thickness, text)
            else:
                img.surround_point(c, color, thickness)

        return img

    # -----------------------------------------------------------------------

    def surround_coord(self, coord, color, thickness, text=""):
        """Add a square surrounding the given coordinates.

        :param coord: (sppasCoords) Area to surround
        :param color: (int, int, int) Rectangle color or brightness (if grayscale image).
        :param thickness: (int) Thickness of lines that make up the rectangle. Negative values, like CV_FILLED , mean that the function has to draw a filled rectangle.
        :param text: (str) Add text

        """
        coord = sppasCoords.to_coords(coord)

        cv2.rectangle(self,
                      (coord.x, coord.y),
                      (coord.x + coord.w, coord.y + coord.h),
                      color,
                      thickness)
        if len(text) > 0:
            (h, w) = self.shape[:2]
            font_scale = (float(w * h)) / (1920. * 1080.)
            th = abs(thickness//2)
            text_size = cv2.getTextSize(text, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                        fontScale=font_scale*2, thickness=th)

            if thickness < 0:
                # the background is using our color... change for foreground
                r, g, b = color
                r = (r + 128) % 255
                g = (g + 128) % 255
                b = (b + 128) % 255
                color = (r, g, b)
            cv2.putText(self, text,
                        (coord.x + (3*th), coord.y + (3*th) + text_size[1]),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, color, th)

    # ----------------------------------------------------------------------------

    def put_text(self, coord, color, thickness, text):
        """Put a text at the given coords.

        :param coord: (sppasCoords) Area to put the text
        :param color: (int, int, int) Rectangle color or brightness (if grayscale image).
        :param thickness: (int) Thickness of lines that make up the rectangle. Negative values, like CV_FILLED , mean that the function has to draw a filled rectangle.
        :param text: (str) Add text

        """
        w, h = self.size()
        coord = sppasCoords.to_coords(coord)
        font_scale = float(w * h) / (1000.*1000.)

        if thickness < 0:
            # the background is using our color... change for foreground
            r, g, b = color
            r = (r + 128) % 255
            g = (g + 128) % 255
            b = (b + 128) % 255
            color = (r, g, b)
        cv2.putText(self, text, (coord.x, coord.y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    # ----------------------------------------------------------------------------

    def surround_point(self, point, color, thickness):
        """Add a circle surrounding the given point.

        :param point: (sppasCoords, list, tuple) (x,y) values to surround
        :param color: (int, int, int) Rectangle color or brightness (if grayscale image).
        :param thickness: (int) Thickness of lines that make up the rectangle. Negative values, like CV_FILLED , mean that the function has to draw a filled rectangle.

        """
        if isinstance(point, sppasCoords) is False:
            if isinstance(point, (tuple, list)) and len(point) >= 2:
                try:
                    point = sppasCoords(point[0], point[1])
                except:
                    pass
        if isinstance(point, sppasCoords) is False:
            sppasTypeError(point, "sppasCoords, tuple, list")

        x = point.x - (thickness * 2)
        y = point.y - (thickness * 2)
        radius = thickness * 2

        cv2.circle(self, (x, y), radius, color, thickness)

    # -----------------------------------------------------------------------
    # Tag the image in a range of coords
    # -----------------------------------------------------------------------

    def ioverlays(self, other, coord1, coord2, nb_img=0, blur=False):
        """Return a list of the image with other overlaid between coords.

        :param other: (sppasImage) Image to overlay
        :param coord1: (sppasCoords) Position and optionally size to overlay - src
        :param coord2: (sppasCoords) Position and optionally size to overlay - dest
        :param nb_img: (int) Total number of images
        :return: (list of sppasImage)

        """
        images = list()
        coord1 = sppasCoords.to_coords(coord1)
        coord2 = sppasCoords.to_coords(coord2)

        # Add the image with other pasted at coord1
        images.append(self.ioverlay(other, coord1))

        # Add nb intermediate images
        if nb_img > 2:
            a, b = slope_intercept((coord1.x, coord1.y), (coord2.x, coord2.y))
            step_x = (coord2.x - coord1.x) / float(nb_img + 1)
            step_y = (coord2.y - coord1.y) / float(nb_img + 1)
            step_w = (coord2.w - coord1.w) / float(nb_img)
            step_h = (coord2.h - coord1.h) / float(nb_img)
            prev_c = coord1
            if blur is True:
                blur_other = other.iblur()
                tr_other = blur_other.ialpha(196, direction=-1)
            for i in range(1, nb_img+1):
                pimg = self.copy()
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
                if blur is True and prev_c.x != c.x and prev_c.y != c.y:
                     tr_step_x = (c.x - prev_c.x) // 3
                     tr_step_y = (c.y - prev_c.y) // 3
                     pimg = self.ioverlay(tr_other, (prev_c.x + tr_step_x, prev_c.y + tr_step_y, prev_c.w, prev_c.h))
                     pimg = pimg.ioverlay(tr_other, (prev_c.x + 2*tr_step_x, prev_c.y + 2*tr_step_y, prev_c.w, prev_c.h))
                     pimg = pimg.ioverlay(tr_other, (prev_c.x + 3*tr_step_x, prev_c.y + 3*tr_step_y, prev_c.w, prev_c.h))

                # put other
                pimg = pimg.ioverlay(other, c)
                images.append(pimg)
                prev_c = c

        # Add the image with other pasted at coord2
        images.append(self.ioverlay(other, coord2))

        return images

    # -----------------------------------------------------------------------

    def irotates(self, angle1, angle2, center=None, scale=1.0, nb_img=0):
        """Return a list of the image rotated ranging the given angles.

        :param angle1: (float) Angle start
        :param angle2: (float) Angle end
        :param center: (tuple) (x,y) position of the rotating center
        :param scale: (float) Scale value
        :param nb_img: (int) Total number of images
        :return: (list of sppasImage)

        """
        images = list()

        # Add the image rotated with angle1 and not scaled
        images.append(self.irotate(angle1, center, scale=1.0))

        # Add nb intermediate images
        if nb_img > 2:
            if scale != 1.0:
                step_scale = (scale-1.0) / float(nb_img + 1)
            else:
                step_scale = 0.
            step_angle = (angle2 - angle1) / float(nb_img + 1)
            for i in range(1, nb_img+1):
                s = 1.0 + (i*step_scale)
                a = angle1 + (i*step_angle)
                pimg = self.irotate(a, center, s)
                images.append(pimg)

        # Add the image rotated with angle2 and scaled
        images.append(self.irotate(angle2, center, scale))

        return images

    # -----------------------------------------------------------------------

    def iscales(self, scale=1.0, nb_img=0):
        """Return a list of the image scaled ranging from 1 to the value.

        :param scale: (float) Scale value
        :param nb_img: (int) Total number of images
        :return: (list of sppasImage)

        """
        return self.irotates(0, 0, None, scale, nb_img)

    # -----------------------------------------------------------------------
    # Save image on disk
    # -----------------------------------------------------------------------

    def write(self, filename):
        """Write the image in to given filename."""
        try:
            cv2.imwrite(filename, self)
        except cv2.error as e:
            logging.error("Error when writing file {}: {}"
                          "".format(filename, str(e)))
            ImageWriteError(filename)

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __eq__(self, other):
        """Allows to write img1 == img2."""
        if len(self) != len(other):
            return False
        for l1, l2 in zip(self, other):
            if len(l1) != len(l2):
                return False
            # the color of the pixel
            for c1, c2 in zip(l1, l2):
                if len(c1) != len(c2):
                    return False
                r1, g1, b1 = c1
                r2, g2, b2 = c2
                if r1 != r2 or g1 != g2 or b1 != b2:
                    return False
        return True

    # -----------------------------------------------------------------------

    def __ne__(self, other):
        return not self.__eq__(other)
