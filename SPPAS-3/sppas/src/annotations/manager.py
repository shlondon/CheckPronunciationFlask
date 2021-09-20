"""
:filename: sppas.src.annotations.manager.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  Automatic annotations manager for SPPAS integrated classes.

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

import logging
import traceback
import sys
import os
from threading import Thread

from sppas.src.config import annots
from sppas.src.wkps import sppasFileUtils
from sppas.src.wkps import States
from sppas.src.anndata import sppasTranscription, sppasTrsRW

import sppas.src.audiodata.aio
import sppas.src.anndata.aio
from sppas.src.videodata import video_extensions

# STANDALONE
from sppas.src.annotations.Activity import sppasActivity
from sppas.src.annotations.Align import sppasAlign
from sppas.src.annotations.FillIPUs import sppasFillIPUs
from sppas.src.annotations.Intsint import sppasIntsint
from sppas.src.annotations.LexMetric import sppasLexMetric
from sppas.src.annotations.Momel import sppasMomel
from sppas.src.annotations.Phon import sppasPhon
from sppas.src.annotations.RMS import sppasRMS
from sppas.src.annotations.SearchIPUs import sppasSearchIPUs
from sppas.src.annotations.SelfRepet import sppasSelfRepet
from sppas.src.annotations.StopWords import sppasStopWords
from sppas.src.annotations.Syll import sppasSyll
from sppas.src.annotations.TextNorm import sppasTextNorm
from sppas.src.annotations.TGA import sppasTGA
from sppas.src.annotations.IVA import sppasIVA

# INTERACTIONS
from sppas.src.annotations.OtherRepet import sppasOtherRepet
from sppas.src.annotations.ReOccurrences import sppasReOcc
from sppas.src.annotations.Overlaps import sppasOverActivity

# SPEAKER
from sppas.src.annotations.SpkLexRep import sppasLexRep

# Annotations on either an image or a video:
from sppas.src.annotations.FaceDetection import sppasFaceDetection
from sppas.src.annotations.FaceSights import sppasFaceSights

# Annotations on a video:
from sppas.src.annotations.FaceClustering import sppasFaceIdentifier
from sppas.src.annotations.CuedSpeech import sppasCuedSpeech

from .infotier import sppasMetaInfoTier
from .log import sppasLog

# ----------------------------------------------------------------------------


class sppasAnnotationsManager(Thread):
    """Parent class for running annotation processes.

    Run annotations on a set of files.

    """

    def __init__(self):
        """Create a new instance.

        Initialize a Thread.

        """
        Thread.__init__(self)

        # fix members that are required to run annotations
        self._parameters = None
        self._progress = None
        self._logfile = sppasLog()

        # fix optional members
        self.__do_merge = True

        # start threading
        self.start()

    # -----------------------------------------------------------------------
    # Options of the manager
    # -----------------------------------------------------------------------

    def set_do_merge(self, do_merge):
        """Fix if the 'annotate' method have to create a merged file or not.

        :param do_merge: (bool) if set to True, a merged file will be created

        """
        self.__do_merge = do_merge

    # ------------------------------------------------------------------------
    # Run annotations
    # ------------------------------------------------------------------------

    def annotate(self, parameters, progress=None):
        """Execute the activated annotations.

        Get execution information from the 'parameters' object.
        Create a Procedure Outcome Report if a filename is set in the
        parameters.

        """
        self._parameters = parameters
        self._progress = progress

        # Print header message in the log-report file or in the logging
        report_file = self._parameters.get_report_filename()
        if report_file:
            try:
                self._logfile = sppasLog(self._parameters)
                self._logfile.create(report_file)
            except:
                self._logfile = sppasLog()
        self._logfile.print_header()
        self._logfile.print_annotations_header()

        # Run all enabled annotations
        ann_stats = [-1] * self._parameters.get_step_numbers()

        for i in range(self._parameters.get_step_numbers()):

            # ignore disabled annotations
            if self._parameters.get_step_status(i) is False:
                continue

            # ok, this annotation is enabled.
            annotation_key = self._parameters.get_step_key(i)
            self._logfile.print_step(i)
            if self._progress:
                self._progress.set_new()
                self._progress.set_header(self._parameters.get_step_name(i))

            try:

                if annotation_key == "fillipus":
                    ann_stats[i] = self._run_fillipus()

                elif annotation_key == "alignment":
                    ann_stats[i] = self._run_alignment()

                elif annotation_key == "rms":
                    ann_stats[i] = self._run_rms()

                elif annotation_key == "facesights":
                    ann_stats[i] = self._run_facesights()

                elif annotation_key == "faceident":
                    ann_stats[i] = self._run_faceident()

                elif annotation_key == "lpc":
                    ann_stats[i] = self._run_lpc()

                else:
                    ann_stats[i] = self._run_annotation(annotation_key)

            except Exception as e:
                self._logfile.print_message(
                    "{:s}\n".format(str(e)), indent=1, status=-1)
                logging.info(traceback.format_exc())
                ann_stats[i] = 0

        # Log file & Merge
        self._logfile.print_separator()
        self._logfile.print_newline()
        if self.__do_merge:
            self._logfile.print_separator()
            self._merge()
        self._logfile.print_stats(ann_stats)
        self._logfile.close()

    # -----------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------------

    def _get_instance_name(self, annotation_key):
        class_name = None
        for i in range(self._parameters.get_step_numbers()):
            a = self._parameters.get_step(i)
            if a.get_key() == annotation_key:
                class_name = a.get_api()
                break
        if class_name is None:
            raise IOError('Unknown annotation key: {:s}'.format(annotation_key))

        return getattr(sys.modules[__name__], class_name)

    # ------------------------------------------------------------------------

    def _create_ann_instance(self, annotation_key):
        """Create and configure an instance of an automatic annotation.

        :param annotation_key: (str) Key of an annotation
        :returns: sppasBaseAnnotation

        """
        # Find the index of this annotation
        step_idx = self._parameters.get_step_idx(annotation_key)

        # Create the instance and fix options
        try:
            auto_annot = self._get_instance_name(annotation_key)(self._logfile)
        except Exception as e:
            self._parameters.disable_step(step_idx)
            self._logfile.print_message(
                "Annotation {} is disabled due to the following error: {}"
                "".format(annotation_key, str(e)))
            return None

        self._fix_ann_options(annotation_key, auto_annot)
        self._fix_ann_extensions(auto_annot)

        # Load language resources
        if self._progress:
            self._progress.set_text("Loading resources...")
        step = self._parameters.get_step(step_idx)
        try:
            auto_annot.load_resources(*step.get_langresource(),
                                      lang=step.get_lang())
        except Exception as e:
            self._parameters.disable_step(step_idx)
            self._logfile.print_message(
                "Annotation {} is disabled due to the following error: {}"
                "".format(annotation_key, str(e)))
            return None

        return auto_annot

    # -----------------------------------------------------------------------

    def _fix_ann_options(self, annotation_key, auto_annot):
        """Set the options to an automatic annotation.

        :param annotation_key: (str) Key of an annotation
        :param auto_annot: (BaseAnnotation)

        """
        # Find the index of this annotation
        step_idx = self._parameters.get_step_idx(annotation_key)

        # Get options from the parameters
        options = self._parameters.get_options(step_idx)

        # Set options to the automatic annotation
        if len(options) > 0:
            auto_annot.fix_options(options)

    # -----------------------------------------------------------------------

    def _fix_ann_extensions(self, auto_annot):
        """Set the output extensions to an automatic annotation.

        :param auto_annot: (BaseAnnotation)

        """
        for out_format in annots.outformat:
            # Get extensions from the parameters and set to the annotation
            ext = self._parameters.get_output_extension(out_format)
            auto_annot.set_out_extension(ext, out_format)

    # -----------------------------------------------------------------------

    def _run_annotation(self, annotation_key):
        """The generic solution to run an automatic annotation.

        :param annotation_key: (str) Key of an annotation
        :returns: number of files processed successfully

        """
        a = self._create_ann_instance(annotation_key)
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file
        files_to_process = self.get_annot_files(pattern=a.get_input_pattern(),
                                                extensions=a.get_input_extensions(),
                                                types=a.get_types())
        # Optional input file(s)
        opt_ext = a.get_opt_input_extensions()
        if len(opt_ext) > 0:
            files = list()
            for f in files_to_process:
                base_f = os.path.splitext(f)[0]
                base_f = base_f.replace(a.get_input_pattern(), "")
                base_f += a.get_input_opt_pattern()

                # Get the optional input file
                other = sppasAnnotationsManager._get_filename(base_f, opt_ext)

                # Append the 2 files
                files.append(([f], [other]))
            files_to_process = files

        if self._logfile:
            self._logfile.print_message("Number of files to process: {}"
                                        "".format(len(files_to_process)), indent=0)
        else:
            logging.info('{:d} files to process'.format(len(files_to_process)))

        out_files = a.batch_processing(files_to_process, self._progress)
        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # -----------------------------------------------------------------------

    def _run_fillipus(self):
        """Execute the FillIPUs automatic annotation.

        Requires an audio file with only one channel and its transcription.

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("fillipus")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        files = list()
        audio_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=self._parameters.get_outformat_extensions("AUDIO"))

        for f in audio_files:
            fn, _ = os.path.splitext(f)
            in_name = fn + ".txt"
            files.append((f, in_name))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # ------------------------------------------------------------------------

    def _run_rms(self):
        """Execute the RMS automatic annotation.

        Requires an audio file and an annotated file with intervals.

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("rms")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file
        annot_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=a.get_input_extensions())

        # Get optional files
        files = list()
        for f in annot_files:
            base_f = os.path.splitext(f)[0]
            base_f = base_f.replace(a.get_input_pattern(), "")

            # Get the audio input file
            audio = sppasAnnotationsManager._get_filename(base_f, sppas.src.audiodata.aio.extensions)

            # Append the 2 files
            files.append(((audio, f), []))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # ------------------------------------------------------------------------

    def _run_alignment(self):
        """Execute the Alignment automatic annotation.

        Requires a phonetization time-aligned with the IPUs.

        Optional is an audio file (required for speech time-alignment but not
        for the alignment of a written text...).

        Optional is a text-normalization time-aligned with the IPUs.

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("alignment")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file is a phonetization
        phon_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=a.get_input_extensions())

        # Get optional files
        files = list()
        for f in phon_files:
            base_f = os.path.splitext(f)[0]
            base_f = base_f.replace(a.get_input_pattern(), "")

            # Get the tokens input file
            extt = list()
            for e in self._parameters.get_outformat_extensions("ANNOT"):
                extt.append(a.get_opt_input_pattern() + e)
            tok = sppasAnnotationsManager._get_filename(base_f, extt)

            # Get the audio input file
            audio = sppasAnnotationsManager._get_filename(
                base_f,
                sppas.src.audiodata.aio.extensions)

            # Append all 3 files
            files.append(([f], (audio, tok)))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # ------------------------------------------------------------------------

    def _run_faceident(self):
        """Execute the FaceIdentity automatic annotation.

        Requires both a video file and a CSV file with coordinates&sights
        of faces

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("faceident")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file is a video
        media_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=a.get_input_extensions())

        # Get optional files
        files = list()
        for f in media_files:
            # Remove any optional pattern
            base_f = os.path.splitext(f)[0]
            base_f = base_f.replace(a.get_input_pattern(), "")

            # Get the CSV input file
            extt = [a.get_opt_input_pattern() + ".csv"]
            csv = sppasAnnotationsManager._get_filename(base_f, extt)
            if csv is not None:
                files.append(([f], [csv]))
                logging.info("Added CSV and video files: {:s}".format(f))
            else:
                logging.info("No CSV file is matching the video {:s}".format(f))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # ------------------------------------------------------------------------

    def _run_facesights(self):
        """Execute the FaceSights automatic annotation.

        Requires a video file or an image.
        Optional is a CSV file with coordinates of faces

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("facesights")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file is an image or a video
        media_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=a.get_input_extensions())

        # Get optional files
        files = list()
        for f in media_files:
            # Remove any optional pattern
            base_f = os.path.splitext(f)[0]
            base_f = base_f.replace(a.get_input_pattern(), "")
            # Get the CSV input file
            extt = [a.get_opt_input_pattern() + ".csv"]
            csv = sppasAnnotationsManager._get_filename(base_f, extt)
            if csv is not None:
                files.append(([f], [csv]))
                logging.info("Added CSV and video files: {:s}".format(f))
            else:
                logging.info("No CSV file is matching the video {:s}".format(f))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # ------------------------------------------------------------------------

    def _run_lpc(self):
        """Execute the LPC automatic annotation.

        Required: time-aligned phonemes.
        Optional: result of FaceClustering (video + landmarks in a CSV file)

        :returns: number of files processed successfully

        """
        a = self._create_ann_instance("lpc")
        if a is None:
            if self._logfile:
                self._logfile.print_message("Annotation is un-available. No files processed.", indent=0)
            return 0

        # Required input file is time-aligned phonemes
        phon_files = self.get_annot_files(
            pattern=a.get_input_pattern(),
            extensions=a.get_input_extensions())

        # Get optional files
        files = list()
        for f in phon_files:
            base_f = os.path.splitext(f)[0]
            base_f = base_f.replace(a.get_input_pattern(), "")

            # Get the CSV with landmarks input file
            extt = [a.get_opt_input_pattern() + ".csv"]
            csv = sppasAnnotationsManager._get_filename(base_f, extt)
            if csv is not None:
                # Get the video input file
                video = sppasAnnotationsManager._get_filename(base_f, video_extensions)
                files.append(([f], (video, csv)))
            else:
                # Append all 3 files
                files.append(([f], ()))

        out_files = a.batch_processing(files, self._progress)

        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # -----------------------------------------------------------------------
    # Manage annotations:
    # -----------------------------------------------------------------------

    def __add_trs(self, trs, trs_inputfile):
        """Add content of trs_inputfile to trs."""
        try:
            parser = sppasTrsRW(trs_inputfile)
            trs_input = parser.read(trs_inputfile)
        except IOError:
            return 0

        # Add tiers
        for tier in trs_input:
            already_in = False
            if trs.is_empty() is False:
                tier_name = tier.get_name()
                for t in trs:
                    if t.get_name() == tier_name:
                        already_in = True
            if already_in is False:
                trs.append(tier)

        # Add metadata
        for key in trs_input.get_meta_keys():
            if trs.get_meta(key, default=None) is None:
                trs.set_meta(key, trs_input.get_meta(key))

        # TODO: Add media in merged trs

        # TODO: Add controlled vocab in merged trs

        # TODO: Add hierarchy links in merged trs

        return 1

    # ------------------------------------------------------------------------

    def _merge(self):
        """Merge all annotated files."""
        self._logfile.print_message("Merge files...", indent=1, status=0)
        if self._progress:
            self._progress.set_header("Merge all annotations in a file")
            self._progress.update(0, "")

        # Get the list of files with the ".wav" extension
        filelist = self.get_annot_files(pattern="", extensions=sppas.src.audiodata.aio.extensions)
        total = len(filelist)

        # get the output extension of any annotation of type ANNOT.
        output_format = self._parameters.get_output_extension("ANNOT")

        for i, f in enumerate(filelist):

            nbfiles = 0

            # Change f, to allow "replace" to work properly
            basef = os.path.splitext(f)[0]

            self._logfile.print_message("File: " + f, indent=0)
            if self._progress:
                self._progress.set_text(os.path.basename(f) + " (" + str(i+1) + "/" + str(total)+")")

            # Add all files content in the same order than to annotate
            trs = sppasTranscription()
            nbfiles += self.__add_trs(trs, basef + output_format)
            for s in range(self._parameters.get_step_numbers()):
                ann_key = self._parameters.get_step_key(s)

                # create an instance of the annotation to get its pattern
                try:
                    a = self._get_instance_name(ann_key)()
                    pattern = a.get_pattern()
                    if len(pattern) > 0:
                        nbfiles += self.__add_trs(trs, basef + pattern + output_format)
                except:
                    # ignore annotations if the corresponding feature is not installed
                    pass

            if nbfiles > 1:
                try:
                    info_tier = sppasMetaInfoTier(trs)
                    tier = info_tier.create_time_tier(
                        trs.get_min_loc().get_midpoint(),
                        trs.get_max_loc().get_midpoint())
                    trs.append(tier)
                    out_file = basef + "-merge" + output_format
                    parser = sppasTrsRW(out_file)
                    parser.write(trs)
                    self._logfile.print_message(out_file, indent=1, status=0)
                    self._parameters.add_to_workspace([out_file])

                except Exception as e:
                    self._logfile.print_message(str(e), indent=1, status=-1)

            if self._progress:
                self._progress.set_fraction(float((i+1))/float(total))
            self._logfile.print_newline()

        if self._progress:
            self._progress.update(1, "Completed.")
            # self._progress.set_header("")

    # -----------------------------------------------------------------------
    # Manage files:
    # -----------------------------------------------------------------------

    def get_annot_files(self, pattern, extensions, types=[]):
        """Search for annotated files with pattern and extensions.

        :param pattern: (str) The pattern to search in the inputs
        :param extensions: (str) The extension to search for
        :param types: (list of str) The types to search in the references of the workspace
        :returns: List of file names matching pattern and extensions

        """
        files = list()
        wkp = self._parameters.get_workspace()

        # create a list with the pattern followed by each possible extension
        if len(pattern) > 0:
            # pat_ext = [pattern + self._parameters.get_output_format()]
            pat_ext = list()
            for e in extensions:
                pat_ext.append(pattern + e)
        else:
            pat_ext = extensions

        roots = wkp.get_fileroot_from_state(States().CHECKED) + \
                wkp.get_fileroot_from_state(States().AT_LEAST_ONE_CHECKED)

        for root in roots:
            new_file = sppasAnnotationsManager._get_filename(root.id, pat_ext)
            if new_file is None:
                continue

            if len(types) == 0 or "STANDALONE" in types:
                files.append(new_file)
            if "SPEAKER" in types:
                other_files = self.__matching_files(root, pat_ext, "SPEAKER")
                for f in other_files:
                    files.append((new_file, f))
            if "INTERACTION" in types:
                other_files = self.__matching_files(root, pat_ext, "INTERACTION")
                for f in other_files:
                    files.append((new_file, f))

        # Remove duplicated entries of the list and return it
        return list(set(files))

    # ------------------------------------------------------------------------

    def __matching_files(self, root, pat_ext, ann_type):
        other_files = list()
        wkp = self._parameters.get_workspace()
        for ref in root.get_references():
            if ref.get_type() == ann_type:
                for fr in wkp.get_fileroot_with_ref(ref):
                    if fr != root:
                        other_file = sppasAnnotationsManager._get_filename(fr.id, pat_ext)
                        if other_file is not None:
                            other_files.append(other_file)
        return other_files

    # ------------------------------------------------------------------------

    @staticmethod
    def _get_filename(rootname, extensions):
        """Return a filename corresponding to one of extensions.

        :param rootname: input file name
        :param extensions: the list of expected extension
        :returns: a file name of the first existing file with an expected
        extension or None

        """
        #base_name = os.path.splitext(filename)[0]
        for ext in extensions:
            ext_filename = rootname + ext
            new_filename = sppasFileUtils(ext_filename).exists()
            if new_filename is not None and os.path.isfile(new_filename):
                return new_filename

        return None
