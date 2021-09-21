# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.imgdata.objdetec.py
:author:   Florian Hocquet, Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic object detection, based on opencv.

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
import numpy
import cv2

from sppas.src.config import sppasError
from sppas.src.config import sppasTypeError
from sppas.src.config import sppasIOError
from sppas.src.config import IntervalRangeException
from sppas.src.config import IOExtensionError
from sppas.src.config import msg

from .coordinates import sppasCoords
from .image import sppasImage

# ---------------------------------------------------------------------------


ERR_MODEL_MISS = msg("At least one model must be loaded first.", "data")

# ---------------------------------------------------------------------------


class BaseObjectsDetector(object):
    """Abstract class to detect objects in an image.

    This class allows to analyze an image in order to detect objects. It
    stores a list of sppasCoords() for each detected object. The detected
    object corresponds to the one of the trained model (human face, human
    profile, cat face, car...).

    :Example:

        >>> f = BaseObjectsDetector()
        >>> f.load_model(model_filename)
        >>> # Detect all the objects in an image
        >>> f.detect(sppasImage(filename="image path"))
        >>> # Get number of detected objects
        >>> len(f)
        >>> # Browse through the detected object coordinates:
        >>> for c in f:
        >>>     print(c)

    An object detector is instantiated from a model. It will be used to
    detect the objects matching the model in an image. Detected objects are
    stored in a list of coordinates. The confidence score of each detected
    object is expected to range [0., 1.].

    Two filters are used to filter detected objects:
        - a min confidence score;
        - a min ratio between the object (w,h) related to the ones of the image.

    """

    DEFAULT_MIN_RATIO = 0.05   # Min object area is 5% of the image
    DEFAULT_MIN_SCORE = 0.28   # Min value of the normalized confidence score

    # -----------------------------------------------------------------------

    def __init__(self):
        """Create a new detector instance.

        """
        # The future detector, instantiated when loading its model
        self._detector = None
        # File extension of the model
        self._extension = ""

        # List of coordinates of detected objects, sorted by confidence score
        self._coords = list()

        # Minimum ratio of an object compared to the image
        self.__min_ratio = BaseObjectsDetector.DEFAULT_MIN_RATIO

        # Minimum confidence score of a detected object
        # It is supposed that the confidence scores of detected objects is
        # ranging [0., 1.]
        self.__min_score = BaseObjectsDetector.DEFAULT_MIN_SCORE

    # -----------------------------------------------------------------------

    def invalidate(self):
        """Invalidate current list of detected object coordinates."""
        self._coords = list()

    # -----------------------------------------------------------------------

    def get_extension(self):
        """Return the expected extension of the model filename."""
        return self._extension

    # -----------------------------------------------------------------------

    def get_min_ratio(self):
        """Return the minimum ratio of an object compared to the image."""
        return self.__min_ratio

    # -----------------------------------------------------------------------

    def set_min_ratio(self, value):
        """Set the minimum ratio of an object compared to the image.

        It means that width and height of a detected object must be at
        least 'value' percent of the image width and height respectively

        :param value: (float) Value ranging [0., 1.]
        :raise: ValueError

        """
        value = BaseObjectsDetector.to_dtype(value, dtype=float)
        if value < 0. or value > 1.:
            raise IntervalRangeException(value, 0., 1.)
        self.__min_ratio = value

    # -----------------------------------------------------------------------

    def get_min_score(self):
        """Return the minimum score of a detected object to consider it."""
        return self.__min_score

    # -----------------------------------------------------------------------

    def set_min_score(self, value):
        """Set the minimum score of a detected object to consider it.

        It means that any detected object with a score lesser than the given
        one will be ignored. The score of detected objects are supposed to
        range between 0. and 1.

        :param value: (float) Value ranging [0., 1.]
        :raise: ValueError

        """
        value = BaseObjectsDetector.to_dtype(value, dtype=float)
        if value < 0. or value > 1.:
            raise IntervalRangeException(value, 0., 1.)
        self.__min_score = value

    # -----------------------------------------------------------------------

    def get_best(self, nb=1):
        """Return a copy of the coordinates with the n-best scores.

        Add "None" if more objects are requested than those detected.

        :param nb: (int) number of coordinates to return
        :return: (list of sppasCoords or sppasCoords or None)

        """
        # No face was previously detected
        if len(self._coords) == 0:
            return None

        # Only the best face is requested.
        nb = BaseObjectsDetector.to_dtype(nb)
        if nb == 1:
            return self._coords[0]

        # Make a copy of the detected coords and select n-best
        nbest = [c.copy() for c in self._coords[:nb]]

        # More objects are requested than those detected
        if nb > len(nbest):
            nbest.extend([None]*(nb-len(nbest)))

        return nbest

    # -----------------------------------------------------------------------

    def get_confidence(self, confidence=0.2):
        """Return a copy of the coordinate objects with the better scores.

        :param confidence: (float) Minimum confidence score ranging [0., 1.]
        :return: (list of sppasCoords or sppasCoords or None)

        """
        # No object was previously detected
        if len(self._coords) == 0:
            return None

        # Verify given comparison score
        score = BaseObjectsDetector.to_dtype(confidence, dtype=float)

        # return the list of sppasCoords with highest confidence
        return [c.copy() for c in self._coords if c.get_confidence() > score]

    # -----------------------------------------------------------------------

    def load_model(self, model, *args):
        """Load at least a model to instantiate a detector.

        :param model: Filename of a model (DNN, HaarCascade, ...)
        :raise: IOError if model is not loaded.

        """
        if model.endswith(self._extension) is False:
            raise IOExtensionError(model)

        if os.path.exists(model) is False:
            raise sppasIOError(model)

        # Create and load the model
        self._set_detector(model)

    # -----------------------------------------------------------------------

    def detect(self, image):
        """Determine the coordinates of all the detected objects.

        :param image: (sppasImage or numpy.ndarray)

        """
        # Invalidate current list of coordinates
        self.invalidate()

        # Convert image to sppasImage if necessary
        if isinstance(image, numpy.ndarray) is True:
            image = sppasImage(input_array=image)
        if isinstance(image, sppasImage) is False:
            raise sppasTypeError("image", "sppasImage")

        # Verify if a model is instantiated
        if self._detector is None:
            raise sppasError(ERR_MODEL_MISS)

        # Detect all objects, without filtering nor sorting.
        # Actually, the "min_ratio" filter is applied by some detectors, so
        # we applied it to all of them - to be consistent.
        self._detection(image)

        # Filter and sort by confidence scores
        self.filter_confidence(self.get_min_score())
        self.sort_by_score()

        try:
            self.filter_overlapped()
            self.sort_by_score()
        except NotImplementedError:
            pass

    # -----------------------------------------------------------------------

    def sort_by_score(self):
        """Sort the detected objects by their confidence score.

        The highest the better.

        """
        # store separately the coords and their scores
        detected = list()
        for coord in self._coords:
            c = coord.copy()
            score = c.get_confidence()
            detected.append((c, score))

        # reset the list of coordinates
        self._coords = list()

        # sort by confidence score (the highest the better) and
        # append into our list of coords
        for coord, score in reversed(sorted(detected, key=lambda x: x[1])):
            self._coords.append(coord)

    # -----------------------------------------------------------------------

    def filter_best(self, nb=1):
        """Filter the coordinates to select only the n-best scores.

        If there are less coordinates than those requested, nothing is
        changed.

        :param nb: (int) number of coordinates to keep

        """
        # check nb value and select the n-best coordinates
        best = self.get_best(nb)
        if nb == 1:
            best = [best]
        # apply only if requested n-best is less than actual size
        if nb < len(self._coords):
            self._coords = best

    # -----------------------------------------------------------------------

    def filter_confidence(self, confidence=0.2):
        """Filter the coordinates to select only the highest scores.

        :param confidence: (float) Minimum confidence score

        """
        # No object was previously detected
        if len(self._coords) == 0:
            return None

        # check confidence value and select the best coordinates
        best = self.get_confidence(confidence)

        # apply only if requested n-best is less than actual size
        if len(best) < len(self._coords):
            self._coords = best

    # -----------------------------------------------------------------------

    @staticmethod
    def to_dtype(value, dtype=int):
        """Convert a value to dtype or raise the appropriate exception.

        :param value: (any type)
        :param dtype: (type) Expected type of the value
        :returns: Value of the given type
        :raises: TypeError

        """
        try:
            value = dtype(value)
            if isinstance(value, dtype) is False:
                raise sppasTypeError(value, str(dtype))
        except ValueError:
            raise sppasTypeError(value, str(dtype))

        return value

    # -----------------------------------------------------------------------
    # Methods to be overridden to create an object detector
    # -----------------------------------------------------------------------

    def _set_detector(self, model):
        """Really load the model and instantiate the detector.

        To be overridden.

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def _detection(self, image):
        """Determine the coordinates of the detected objects.

        To be overridden.

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def filter_overlapped(self, overlap=50.):
        """Remove overlapping detected objects.

        To be overridden.

        """
        pass

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __len__(self):
        return len(self._coords)

    # -----------------------------------------------------------------------

    def __iter__(self):
        for coordinates in self._coords:
            yield coordinates

    # ----------------------------------------------------------------------

    def __getitem__(self, i):
        return self._coords[i]

    # ----------------------------------------------------------------------

    def __contains__(self, value):
        """Return true if value in self.__coordinates."""
        for c in self._coords:
            if c == value:
                return True
        return False

    # -----------------------------------------------------------------------

    def __str__(self):
        return "\n".join([str(c) for c in self._coords])

    # -----------------------------------------------------------------------

    def __repr__(self):
        return self.__class__.__name__

    # -----------------------------------------------------------------------

    def __format__(self, fmt):
        return str(self).__format__(fmt)

# ---------------------------------------------------------------------------
# OpenCV HaarCascadeClassifier for objects detection
# ---------------------------------------------------------------------------


class HaarCascadeDetector(BaseObjectsDetector):
    """Detect objects in an image with Haar Cascade Classifier.

    The HaarCascadeClassifier, when used to detect objects, is returning a
    list of detections, with weights instead of confidence scores. This class
    converts weights into scores ranging [0.998, min_ratio] with a modified
    version of the Unity-based normalization method.

    This classifier already delete overlapped detections and allows to fix
    a threshold size to filter too small objects.

    """

    def __init__(self):
        super(HaarCascadeDetector, self).__init__()
        self._extension = ".xml"

    # -----------------------------------------------------------------------

    def _set_detector(self, model):
        """Initialize the detector with the given file.

        :param model: (str) Filename of the XML Haar Cascade file
        :raises: Exception

        """
        try:
            self._detector = cv2.CascadeClassifier(model)
        except cv2.error as e:
            logging.error("Loading the XML Haar Cascade model failed.")
            raise sppasError(str(e))

    # -----------------------------------------------------------------------

    def _detection(self, image):
        """Determine the coordinates of the detected objects.

        :param image: (sppasImage or numpy.ndarray)

        """
        # make predictions
        detections = self.__haar_detections(image)

        # Convert detections into a list of sppasCoords
        if len(detections[0]) == 0:
            return

        # Detection weights normalization into confidence scores
        scores = self.normalize_weights([d[0] for d in detections[2]])

        # convert the detected positions into a list of sppasCoords
        for rect, score in zip(detections[0], scores):
            coords = sppasCoords(rect[0], rect[1], rect[2], rect[3])
            coords.set_confidence(score)
            # Enable the condition as soon as weight are normalized into scores
            # if score > self.get_min_score():
            self._coords.append(coords)

    # -----------------------------------------------------------------------

    def __haar_detections(self, image, scale_factor=1.06):
        """Detect objects using the Haar Cascade classifier.

        This classifier already delete overlapped detections and too small
        detected objects. Returned detections are a tuple with 3 values:
            - a list of N-list of rectangles;
            - a list of N times the same int value (why???);
            - a list of N weight values.

        Notice that the scale factor has a big impact on the estimation time:
            - with 1.04 => 5.3x real time,
            - with 1.10 => 2.2x real time, but -6% of detected objects (relevant ones?)

        :param image: (sppasImage)
        :param scale_factor: (float) how much the image size is reduced at each image scale
        :return: (numpy arrays)

        """
        # Ignore too small detections, ie less than 5% of the image size
        w, h = image.size()
        min_w = int(float(w) * self.get_min_ratio())
        min_h = int(float(h) * self.get_min_ratio())
        try:
            detections = self._detector.detectMultiScale3(
                image,
                scaleFactor=scale_factor,
                minNeighbors=3,    # how many neighbors each candidate rectangle should have to retain it
                minSize=(min_w, min_h),  # minimum possible object size. Objects smaller than that are ignored.
                flags=0,
                outputRejectLevels=True  # cv2.error if set to False
            )

        except cv2.error as e:
            self._coords = list()
            raise sppasError("HaarCascadeClassifier detection failed: {}"
                             "".format(str(e)))

        return detections

    # -----------------------------------------------------------------------

    def normalize_weights(self, dataset):
        """Return the normalized list of values.

        Use the Unity-based normalization, slightly adapted.

        :param dataset: (list) List of float weight values
        :returns: list of confidence scores

        """
        a = self.get_min_score()
        b = 0.998
        coeff = b-a
        norm_list = list()
        if isinstance(dataset, list):
            min_value = min(dataset) * b     # multiplying by b = custom
            max_value = max(dataset) * 1.01  # multiplying by 1.01 = custom

            for value in dataset:
                tmp = a + ((value - min_value)*coeff) / (max_value - min_value)
                norm_list.append(min(1., max(0., tmp)))

        return norm_list

# ---------------------------------------------------------------------------
# OpenCV Artifical Neural Networks for objects detection
# ---------------------------------------------------------------------------


class BaseNeuralNetDetector(BaseObjectsDetector):
    """Detect objects in an image with an Artificial Neural Network.

    OpenCV DNN supports 2 networks:

        1. FP16 version of the original Caffe implementation (5.4 MB)
        2. 8 bit Quantized version using TensorFlow (2.7 MB)

    """

    def __init__(self):
        super(BaseNeuralNetDetector, self).__init__()

    # -----------------------------------------------------------------------

    def _detection(self, image):
        """Determine the coordinates of the detected objects.

        :param image: (sppasImage or numpy.ndarray)

        """
        # make predictions
        try:
            detections = self._net_detections(image)
        except cv2.error as e:
            raise sppasError("DNN detection failed: {}".format(str(e)))

        # Loops over the detections and for each object in detection
        # get the confidence score.
        w, h = image.size()
        self._coords = list()
        for i in range(detections.shape[2]):
            # Sets the confidence score of the current object
            confidence = detections[0, 0, i, 2]

            # Filter out weak detections by ignoring too small objects,
            # i.e. less than 5% of the image size.
            new_coords = self.__to_coords(detections, i, w, h, confidence)
            if new_coords.w > int(float(w) * self.get_min_ratio()) and new_coords.h > int(
                    float(h) * self.get_min_ratio()):
                self._coords.append(new_coords)

    # -----------------------------------------------------------------------

    def _net_detections(self, image):
        """To be overridden. Initialize net and blob for the processing.

        :returns: detections.

        """
        raise NotImplementedError

    # -----------------------------------------------------------------------

    def filter_overlapped(self, overlap=50.):
        """Remove overlapping detected objects.

        :param overlap: (float) Minimum percentage of the overlapped area
        to invalidate a detected object.

        """
        selected = [c for c in self._coords]
        self._coords = list()
        for i, coord in enumerate(selected):
            # does this coord is overlapping some other ones?
            keep_me = True
            for j, other in enumerate(selected):
                if i != j and coord.intersection_area(other) > 0:
                    # if we did not already invalidated other
                    if other.get_confidence() > 0.:
                        area_o, area_s = coord.overlap(other)
                        # reject this object if more than 50% of its area is
                        # overlapping another one and the other one has a
                        # bigger dimension, either w or h or both
                        if area_s > overlap and (coord.w < other.w or coord.h < other.h):
                            # Invalidate this coord. It won't be considered anymore.
                            keep_me = False
                            coord.set_confidence(0.)
                            break

            if keep_me is True:
                self._coords.append(coord)

    # -----------------------------------------------------------------------

    def __to_coords(self, detections, index, width, height, confidence):
        """Convert net detections into a list of sppasCoords.

        :returns: A list of coordinates objects.

        """
        # Determines the hitbox of the current object
        x = int(detections[0, 0, index, 3] * width)
        y = int(detections[0, 0, index, 4] * height)
        w = int(detections[0, 0, index, 5] * width) - x
        h = int(detections[0, 0, index, 6] * height) - y
        # or:
        # box = detections[0, 0, index, 3:7] * numpy.array([width, height, width, height])
        # (startX, startY, endX, endY) = box.astype("int")
        # x, y, w, h = startX, startY, endX - startX, endY - startY

        # check if values are correct
        if x < 0:
            x = 0
        if y < 0:
            y = 0

        # Then creates a sppasCoords object with these values
        return sppasCoords(x, y, w, h, confidence)

# ---------------------------------------------------------------------------


class NeuralNetCaffeDetector(BaseNeuralNetDetector):
    """Detect objects in an image with an Artificial Neural Network.

    """

    def __init__(self):
        super(NeuralNetCaffeDetector, self).__init__()
        self._extension = ".caffemodel"

    # -----------------------------------------------------------------------

    def _set_detector(self, model):
        """Initialize the model with the given file.

        :param model: (str) Filename of the Caffe model file
        :raise: IOError, Exception

        """
        fn, fe = os.path.splitext(model)
        proto = fn + ".prototxt"
        if os.path.exists(proto) is False:
            raise sppasIOError(proto)

        try:
            self._detector = cv2.dnn.readNetFromCaffe(proto, model)
        except cv2.error as e:
            logging.error("Artificial Neural Network model or proto "
                          "(Caffe) failed to be read.")
            raise sppasError(str(e))

    # -----------------------------------------------------------------------

    def _net_detections(self, image):
        """Initialize net and blob for the processing.

        :returns: detections.

        """
        # Load the image and construct an input blob for the image.
        # This blob corresponds to the defaults proto and model.
        # blobFromImages creates 4-dimensional blob from image.
        # Optionally resizes and crops image from center, subtract mean
        # values, scales values by scalefactor, swap Blue and Red channels.
        # blobFromImage(image, scalefactor=1.0, size, mean, swapRB=False, crop=False)
        # but, to resize, I prefer my own solution: width will be proportional
        img = image.iresize(width=0, height=360)
        w, h = img.size()
        # In all tutorials, the following image conversion is given:
        # blob = cv2.dnn.blobFromImage(image, 1.0, (w, h), (104, 177, 123))
        # all but one different gives better result -- as far as I tested:
        blob = cv2.dnn.blobFromImage(img, 1.0, (w, h), (103.93, 116.77, 123.68))

        # To detect faces, pass the blob through the net to analyze it
        self._detector.setInput(blob)

        # Runs forward pass to compute output of layer.
        # Then return the detections. They contain predictions about
        # what the image contains, type: "numpy.ndarray"
        return self._detector.forward()

# ---------------------------------------------------------------------------


class NeuralNetTensorFlowDetector(BaseNeuralNetDetector):
    """Detect objects in an image with an Artificial Neural Network.

    """

    def __init__(self):
        super(NeuralNetTensorFlowDetector, self).__init__()
        self._extension = ".pb"

    # -----------------------------------------------------------------------

    def _set_detector(self, model):
        """Initialize the model with the given file.

        :param model: (str) Filename of the Caffe model file
        :raise: IOError, Exception

        """
        fn, fe = os.path.splitext(model)
        proto = fn + ".pbtxt"
        if os.path.exists(proto) is False:
            raise sppasIOError(proto)

        try:
            self._detector = cv2.dnn.readNetFromTensorflow(model, proto)
        except cv2.error as e:
            logging.error("Artificial Neural Network model or proto "
                          "(TensorFlow) failed to be read.")
            raise sppasError(str(e))

    # -----------------------------------------------------------------------

    def _net_detections(self, image):
        """Initialize net and blob for the processing.

        :returns: detections.

        """
        # Load the image and construct an input blob
        img = image.iresize(width=0, height=360)
        w, h = img.size()
        blob = cv2.dnn.blobFromImage(img, 1.0, (w, h), (103.93, 116.77, 123.68), False, False)

        # To detect faces, pass the blob through the net to analyze it
        self._detector.setInput(blob)

        # Runs forward pass to compute output of layer.
        # Then return the detections. They contain predictions about
        # what the image contains, type: "numpy.ndarray"
        return self._detector.forward()

# ---------------------------------------------------------------------------


class NeuralNetONNXDetector(BaseNeuralNetDetector):
    """Detect objects in an image with an Artificial Neural Network.

    * * * * *   Not tested (no free model found) * * * * *

    """

    def __init__(self):
        super(NeuralNetONNXDetector, self).__init__()
        self._extension = ".onnx"

    # -----------------------------------------------------------------------

    def _set_detector(self, model):
        """Initialize the model with the given file.

        :param model: (str) Filename of the Caffe model file
        :raise: IOError, Exception

        """
        try:
            self._detector = cv2.dnn.readNetFromONNX(model)
        except cv2.error as e:
            logging.error("Artificial Neural Network model "
                          "(ONNX) failed to be read.")
            raise sppasError(str(e))

    # -----------------------------------------------------------------------

    def _net_detections(self, image):
        """Initialize net and blob for the processing.

        :returns: detections.

        """
        # Load the image and construct an input blob for the image.
        # This blob corresponds to the default model
        blob = cv2.dnn.blobFromImage(image, 1.0, (320, 240), (127, 127, 127), False, False)

        # To detect faces, pass the blob through the net to analyze it
        self._detector.setInput(blob)

        # Runs forward pass to compute output of layer.
        # Then return the detections. They contain predictions about
        # what the image contains, type: "numpy.ndarray"
        return self._detector.forward()

# ---------------------------------------------------------------------------
# Detect object with a detector
# ---------------------------------------------------------------------------


class sppasImageObjectDetection(BaseObjectsDetector):
    """Detect objects in an image.

    This class allows to analyze an image in order to detect objects. It
    stores a list of sppasCoords() for each detected object.

    :Example:

        >>> f = sppasImageObjectDetection()
        >>> f.load_model(filename1, filename2...)
        >>> # Detect all the objects in an image
        >>> f.detect(sppasImage(filename="image path"))
        >>> # Get number of detected objects
        >>> len(f)
        >>> # Browse through the detected object coordinates:
        >>> for c in f:
        >>>     print(c)
        >>> # Get the detected object with the highest score
        >>> f.get_best()
        >>> # Get the 2 objects with the highest scores
        >>> f.get_best(2)
        >>> # Get detected objects with a confidence score greater than 0.9
        >>> f.get_confidence(0.9)

    Contrariwise to the base class, this class allows multiple models
    in order to launch multiple detections and to combine their results.

    """

    # List of implemented detectors and expected file extension of the model.
    DETECTORS = dict()
    DETECTORS[HaarCascadeDetector().get_extension().lower()] = HaarCascadeDetector
    DETECTORS[NeuralNetCaffeDetector().get_extension().lower()] = NeuralNetCaffeDetector
    DETECTORS[NeuralNetTensorFlowDetector().get_extension().lower()] = NeuralNetTensorFlowDetector
    DETECTORS[NeuralNetONNXDetector().get_extension().lower()] = NeuralNetONNXDetector

    # -----------------------------------------------------------------------

    def __init__(self):
        """Create a new ImageObjectDetection instance."""
        super(sppasImageObjectDetection, self).__init__()
        self._extension = ""

    # -----------------------------------------------------------------------

    def get_nb_recognizers(self):
        """Return the number of initialized object recognizers."""
        if self._detector is None:
            return 0
        return len(self._detector)

    # -----------------------------------------------------------------------

    def load_model(self, model, *args):
        """Instantiate detector(s) from the given models.

        Calling this method invalidates the existing detectors.

        :param model: (str) Default required model filename
        :param args: Other models to load in order to create object detectors
        :raise: IOError, Exception

        """
        self._detector = list()
        detector = sppasImageObjectDetection.create_detector_from_extension(model)
        detector.load_model(model)
        self._detector.append(detector)

        for filename in args:
            try:
                detector = sppasImageObjectDetection.create_detector_from_extension(filename)
                detector.load_model(filename)
                self._detector.append(detector)
            except Exception as e:
                logging.error(e)

        for detector in self._detector:
            detector.set_min_ratio(self.get_min_ratio() / len(self._detector))

    # -----------------------------------------------------------------------

    @staticmethod
    def extensions():
        """Return the whole list of supported extensions in lower case."""
        return list(sppasImageObjectDetection.DETECTORS.keys())

    # -----------------------------------------------------------------------

    @staticmethod
    def create_detector_from_extension(filename):
        """Return an object detector according to a given filename.

        Only the extension of the filename is used.

        :param filename: (str)
        :return: BaseObjectsDetector
        :raise: IOError

        """
        extension = os.path.splitext(filename)[1]
        extension = extension.lower()
        if extension in sppasImageObjectDetection.extensions():
            return sppasImageObjectDetection.DETECTORS[extension]()

        raise IOExtensionError(filename)

    # -----------------------------------------------------------------------

    def _detection(self, image):
        """Determine the coordinates of all the detected objects.

        No filter nor sort is applied. Results are "as it".

        :param image: (sppasImage or numpy.ndarray)

        """
        for i in range(len(self._detector)):
            self._detector[i].detect(image)
            # Add detected objects to our list
            for coord in self._detector[i]:
                self._coords.append(coord)

        # logging.debug(" ... All detected objects of the {:d} predictors:"
        #               "".format(len(self._detector)))
        # for coord in self._coords:
        #     logging.debug(" ... ... {}".format(coord))

    # -----------------------------------------------------------------------

    def filter_overlapped(self, overlap=50., norm_score=True):
        """Remove overlapping detected objects and too small scores.

        It is supposed that the scores are already sorted by scores.

        :param overlap: (float) Minimum percentage of overlapped area to invalidate an object
        :param norm_score: (bool) Normalize the score of the detected objects by the number of detectors

        """
        overlap = float(overlap)
        if overlap < 0. or overlap > 100.:
            raise IntervalRangeException(overlap, 0., 100.)

        # **** NO: Divide the score by the number of detectors
        detected = list()
        for coord in self._coords:
            c = coord.copy()
            score = c.get_confidence()
            if norm_score is True:
                c.set_confidence(score / float(len(self._detector)))
            detected.append(c)

        # Reduce the list of detected objects by selecting overlapping
        # objects and adjust their scores:
        #    - add confidence score to the one we keep and
        #    - cancel confidence score of the one we remove
        for i, coord in enumerate(detected):
            # does this coord is overlapping some other ones?
            for j, other in enumerate(detected):
                # if we did not already cancelled the other coordinates
                if other.get_confidence() == 0. or i == j:
                    continue
                # if i and j are overlapping
                if coord.intersection_area(other) > 0:
                    # how much are they overlapping?
                    area_o, area_s = coord.overlap(other)
                    # reject j object if more than 50% of its area is
                    # overlapping i. (normally i has a better score)
                    if area_o > overlap:
                        c = min(1., other.get_confidence() + coord.get_confidence())
                        coord.set_confidence(c)
                        other.set_confidence(0.)
                    """
                    # reject "i" object if more than 50% of its area is
                    # overlapping "j" and "j" has a significant bigger 
                    # dimension, either w or h or both
                    if area_s > overlap and (coord.w < other.w or coord.h < other.h):
                        c = min(1., other.get_confidence() + coord.get_confidence())
                        coord.set_confidence(0.)
                        other.set_confidence(c)
                    """

        # Select results for norm_score = True or False
        # selected = list()
        # for c in detected:
        #     if c.get_confidence() > 1.:
        #         c.set_confidence(1.)
        #     if c.get_confidence() > 0:
        #         selected.append(c)

        # Finally, keep only detected objects if their score is higher then
        # the min score we fixed
        self._coords = [c for c in detected if c.get_confidence() > self.get_min_score()]

