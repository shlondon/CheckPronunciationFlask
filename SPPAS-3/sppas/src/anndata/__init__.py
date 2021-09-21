# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.anndata.__init__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Package to manage annotated data.

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

*****************************************************************************
anndata: management of transcribed data.
*****************************************************************************

anndata is a free and open source Python library to access and
search data from annotated data. It can convert file formats like Elan’s EAF,
Praat's TextGrid and others into a sppasTranscription() object and convert
into any of these formats. Those objects allow unified access to linguistic
data from a wide range sources.

It requires the following other packages:

* config
* utils
* wkps

"""

from .aio import serialize_labels
from .aio import serialize_label
from .aio import format_labels
from .aio import format_label
from .aio.readwrite import sppasTrsRW
from .aio.readwrite import FileFormatProperty
from .metadata import sppasMetaData
from .transcription import sppasTranscription
from .tier import sppasTier
from .ctrlvocab import sppasCtrlVocab
from .media import sppasMedia
from .hierarchy import sppasHierarchy
from .ann.annlabel import sppasLabel
from .ann.annlabel import sppasTag
from .ann.annlabel import sppasTagCompare
from .ann.annlocation import sppasLocation
from .ann.annlocation import sppasDuration
from .ann.annlocation import sppasDurationCompare
from .ann.annlocation import sppasInterval
from .ann.annlocation import sppasPoint
from .ann.annlocation import sppasDisjoint
from .ann.annotation import sppasAnnotation
from .ann.annset import sppasAnnSet

__all__ = (
    'sppasMetaData',
    'sppasTrsRW',
    'FileFormatProperty',
    'sppasTranscription',
    'sppasTier',
    'sppasAnnotation',
    'sppasCtrlVocab',
    'sppasMedia',
    'sppasHierarchy',
    'sppasLabel',
    'sppasTag',
    'sppasTagCompare',
    'sppasLocation',
    'sppasDuration',
    'sppasDurationCompare',
    'sppasDisjoint',
    'sppasInterval',
    'sppasPoint',
    'sppasAnnSet',
    'serialize_labels',
    'serialize_label',
    'format_labels',
    'format_label'
)
