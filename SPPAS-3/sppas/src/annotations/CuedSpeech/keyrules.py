# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.CuedSpeech.keyrules.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Parse a rule file of Cued Speech keys.

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
import logging

from sppas.src.config import symbols, separators
from sppas.src.utils.makeunicode import sppasUnicode

# ----------------------------------------------------------------------------


class KeyRules(object):
    """Manager of a set of rules for syllabification of Cued Speech keys.

    Format of the rules:

    PHONCLASS i V
    PHONCLASS e V
    ...
    PHONCLASS p C
    PHONCLASS t C
    PHONCLASS cnil C
    PHONCLASS vnil V

    PHONKEY cnil 5
    PHONKEY vnil 3
    PHONKEY i 4
    PHONKEY e 5
    PHONKEY p 1
    PHONKEY t 5
    ...

    """

    BREAK_SYMBOL = "#"

    # -----------------------------------------------------------------------

    def __init__(self, filename=None):
        """Create a new instance.

        :param filename: (str) Name of the file with the rules.

        """
        # key = phoneme or symbol;
        # value = tuple(class, key code)
        self.__phon = dict()

        if filename is not None:
            self.load(filename)
        else:
            self.reset()

    # ------------------------------------------------------------------------

    def reset(self):
        """Reset the set of rules."""
        self.__phon = dict()
        for phone in symbols.all:
            self.__phon[phone] = (KeyRules.BREAK_SYMBOL, None)

        self.__phon["vnil"] = ("V", "0")
        self.__phon["cnil"] = ("C", "5")

    # ------------------------------------------------------------------------

    def load(self, filename):
        """Load the rules from a file.

        :param filename: (str) Name of the file with the rules.
        :returns: (bool) Rules were appended or not

        """
        self.reset()
        if os.path.exists(filename):
            with open(filename, "r") as f:
                lines = f.readlines()
                f.close()
        else:
            logging.error("Unknown Cued Speech rules file {}".format(filename))
            return False

        added = False
        for line_nb, line in enumerate(lines, 1):
            sp = sppasUnicode(line)
            line = sp.to_strip()
            wds = line.split()
            if len(wds) == 3:
                # The string representing the phoneme is the key of the self.__phon dict.
                p = wds[1]
                if p not in self.__phon:
                    # create a new entry in the dictionary of phonemes
                    self.__phon[p] = (None, None)

                # fill-in the value of the phoneme entry in the dict
                tup = self.__phon[p]
                if wds[0] == "PHONCLASS":
                    # PHONCLASS allows to fill-in the phoneme class.
                    # we won't change the key
                    self.__phon[wds[1]] = (wds[2], tup[1])
                    added = True

                elif wds[0] == "PHONKEY":
                    # PHONKEY allows to fill-in the phoneme key
                    # we won't change the class
                    self.__phon[wds[1]] = (tup[0], wds[2])
                    added = True

        return added

    # ------------------------------------------------------------------------

    def get_class(self, phoneme):
        """Return the class identifier of the phoneme.

        If the phoneme is unknown, the break symbol is returned.

        :param phoneme: (str) A phoneme
        :returns: class of the phoneme or break symbol

        """
        tup = self.__phon.get(phoneme, None)
        if tup is None:
            return KeyRules.BREAK_SYMBOL
        return tup[0]

    # ------------------------------------------------------------------------

    def get_key(self, phoneme):
        """Return the key identifier of the phoneme.

        If the phoneme is unknown, None is returned.
        If the phoneme is a break, None is returned.
        If no key was defined for this phoneme, the "nil" key is returned.

        :param phoneme: (str) A phoneme
        :returns: key of the phoneme or None

        """
        tup = self.__phon.get(phoneme, None)
        if tup is None:
            return None

        # The key like defined in the config file
        key = tup[1]

        # If no key was defined for this phoneme, use nil.
        if key is None:
            if tup[0] == "V":
                key = self.__phon["vnil"][1]
            elif tup[0] == "C":
                key = self.__phon["cnil"][1]

        return key

    # ------------------------------------------------------------------------

    def get_nil_consonant(self):
        """Return the key code for a missing consonant."""
        return self.__phon['cnil'][1]

    # ------------------------------------------------------------------------

    def get_nil_vowel(self):
        """Return the key code for a missing vowel."""
        return self.__phon['vnil'][1]

    # ------------------------------------------------------------------------

    def syll_key(self, syll):
        """Return the key codes matching the given syllable.

        The given entry can be either of the form CV or C or V.

        :param syll: (str) A syllable like "p-a", or "p" or "a".
        :returns: tuple(str, str) representing a CV key code
        :raises: ValueError

        """
        phons = syll.split(separators.phonemes)
        if len(phons) == 0:
            raise ValueError("A LPC-syllable should contain at least one phoneme."
                             "Got {} instead.".format(syll))
        if len(phons) > 2:
            raise ValueError("A LPC-syllable should contain at max two phonemes."
                             "Got {} instead.".format(syll))

        if len(phons) == 1:
            if self.get_class(phons[0]) == "V":
                phons.insert(0, "cnil")
            elif self.get_class(phons[0]) == "C":
                phons.append("vnil")
            else:
                phons.insert(0, "unknown")

        if self.get_class(phons[0]) != "C" or self.get_class(phons[1]) != "V":
            raise ValueError("A LPC-syllable should contain a C-V sequence of phonemes."
                             "Got {} instead.".format(syll))

        return self.get_key(phons[0]), self.get_key(phons[1])

