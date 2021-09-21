# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.annotations.CuedSpeech.lpckeys.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Keys generation of the Cued Speech from time-aligned phonemes.

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

from sppas.src.config import separators

from .keyrules import KeyRules

# ----------------------------------------------------------------------------


class CuedSpeechKeys(object):
    """Cued Speech keys generation from a sequence of phonemes.

    """

    def __init__(self, keys_filename=None):
        """Create a new LPC instance.

        Load keys from a text file, depending on the language and phonemes
        encoding. See documentation for details about this file.

        :param keys_filename: (str) Name of the file with the list of keys.

        """
        self.rules = KeyRules(keys_filename)

    # -----------------------------------------------------------------------

    def syllabify(self, phonemes, durations=()):
        """Return the key boundaries of a sequence of phonemes.

        Perform the segmentation of the sequence of phonemes into the
        syllables-structure of the LPC coding scheme.
        A syllable is CV, or V or C.

        >>> phonemes = ['b', 'O~', 'Z', 'u', 'R']
        >>> CuedSpeechKeys("fra-config-file").syllabify(phonemes)
        >>> [ (0, 1), (2, 3), (4, 4) ]

        :param phonemes: (list of str) List of phonemes
        :param durations: (list of float) List of phoneme' durations
        :returns: list of tuples (begin index, end index)

        """
        # Convert a list of phonemes into a list of key classes.
        classes = [self.rules.get_class(p) for p in phonemes]
        syll = list()

        i = 0
        while i < len(phonemes):
            c = classes[i]
            if c in ("V", "C"):
                if i+1 == len(phonemes):
                    # we reach the end of the list of phonemes but a phoneme
                    # is still in the list.
                    syll.append((i, i))
                else:
                    c_next = classes[i+1]
                    if c == "V":
                        # The current phoneme is a vowel
                        syll.append((i, i))
                    else:
                        # The current phoneme is a consonant
                        if c_next == "V":
                            # The next phoneme is a vowel
                            syll.append((i, i+1))
                            i += 1
                        else:
                            if c_next == "C":
                                # The next phoneme is a consonant too
                                if len(durations) == len(phonemes):
                                    if durations[i] > 0.04:
                                        syll.append((i, i))
                                    # Ignore an isolated consonant if very short duration.
                                else:
                                    syll.append((i, i))

                            else:
                                # The next phoneme is neither a vowel nor a consonant.
                                syll.append((i, i))

            i += 1

        return syll

    # -----------------------------------------------------------------------
    # Output formatting
    # -----------------------------------------------------------------------

    @staticmethod
    def phonetize_syllables(phonemes, syllables):
        """Return the phonetized sequence of syllables.

        >>> phonemes = ['b', 'O~', 'Z', 'u', 'R']
        >>> lpc_keys = CuedSpeechKeys("fra-config-file")
        >>> syllables = lpc_keys.syllabify(phonemes)
        >>> lpc_keys.phonetize_syllables(phonemes, syllables)
        >>> "b-O~.Z-u.R"

        :param phonemes: (list) List of phonemes
        :param syllables: list of tuples (begin index, end index)
        :returns: (str) String representing the syllables segmentation

        The output string is using the X-SAMPA standard to indicate the
        phonemes and syllables segmentation.

        """
        str_syll = list()
        for (begin, end) in syllables:
            str_syll.append(separators.phonemes.join(phonemes[begin:end+1]))

        return separators.syllables.join(str_syll)

    # -----------------------------------------------------------------------

    def syll_to_key(self, phonetized_syllable):
        """Return the key (c, v) of a phonetized syllable.

        >>> syllable = "p-a"
        >>> lpc_keys.syll_to_key(syllable)
        >>> ("1", "3")

        :param phonetized_syllable: (str) the phonemes of the syllable
        :return: (tuple)

        """
        return self.rules.syll_key(phonetized_syllable)

    # -----------------------------------------------------------------------

    def keys_phonetized(self, phonetized_syllables):
        """Return the keys of a phonetized syllable as C-V sequences.

        The input string is using the X-SAMPA standard to indicate the
        phonemes and syllables segmentation.

        >>> syllable = "e.p-a.R"
        >>> lpc_keys = CuedSpeechKeys("fra-config-file")
        >>> lpc_keys.keys_phonetized(syllable)
        >>> "0-5.1-3.8-0"

        :param phonetized_syllables: (str) String representing the keys segments
        :return: (str)

        """
        c = list()
        for syll in phonetized_syllables.split(separators.syllables):
            try:
                consonant, vowel = self.rules.syll_key(syll)
                c.append(consonant + separators.phonemes + vowel)
            except ValueError:
                c.append(separators.phonemes)

        return separators.syllables.join(c)
