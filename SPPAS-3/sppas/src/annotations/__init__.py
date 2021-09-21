# -*- coding: UTF-8 -*-
"""
    ..
        ---------------------------------------------------------------------
         ___   __    __    __    ___
        /     |  \  |  \  |  \  /              the automatic
        \__   |__/  |__/  |___| \__             annotation and
           \  |     |     |   |    \             analysis
        ___/  |     |     |   | ___/              of speech

        http://www.sppas.org/

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

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      develop@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

*****************************************************************************
annotations: automatic annotations.
*****************************************************************************

This package includes all the automatic annotations, each one in a
package and classes to manage the data to be annotated and the resulting
annotated data.

Requires the following other packages:

* config
* utils
* exc
* structs
* wkps
* resources
* anndata
* audiodata
* imgdata    -- if "video" feature enabled
* videodata  -- if "video" feature enabled

"""

from .autils import SppasFiles
from .Activity import sppasActivity
from .Align import sppasAlign
from .FillIPUs import sppasFillIPUs
from .Intsint import sppasIntsint
from .LexMetric import sppasLexMetric
from .Momel import sppasMomel
from .OtherRepet import sppasOtherRepet
from .Phon import sppasPhon
from .ReOccurrences import sppasReOcc
from .RMS import sppasRMS
from .SearchIPUs import sppasSearchIPUs
from .SelfRepet import sppasSelfRepet
from .SpkLexRep import sppasLexRep
from .StopWords import StopWords
from .StopWords import sppasStopWords
from .Syll import sppasSyll
from .TextNorm import sppasTextNorm
from .TGA import sppasTGA
from .IVA import sppasIVA
from .Overlaps import sppasOverActivity

from .FaceDetection import sppasFaceDetection
from .FaceSights import sppasFaceSights
from .FaceSights import ImageFaceLandmark
from .CuedSpeech import sppasCuedSpeech

from .searchtier import sppasFindTier
from .param import sppasParam
from .manager import sppasAnnotationsManager

# ---------------------------------------------------------------------------


__all__ = (
    'SppasFiles',
    'sppasMomel',
    'sppasIntsint',
    'sppasFillIPUs',
    'sppasSearchIPUs',
    'sppasTextNorm',
    'sppasPhon',
    'sppasAlign',
    'sppasSyll',
    'sppasTGA',
    'sppasIVA',
    'sppasSelfRepet',
    'sppasActivity',
    'sppasRMS',
    'sppasOtherRepet',
    "sppasOverActivity",
    'StopWords',
    'sppasStopWords',
    'sppasLexMetric',
    'sppasReOcc',
    'sppasFindTier',
    'sppasParam',
    'sppasAnnotationsManager',
    'sppasLexRep',
    'sppasFaceDetection',
    'sppasFaceSights',
    "ImageFaceLandmark",
    'sppasCuedSpeech'
)
