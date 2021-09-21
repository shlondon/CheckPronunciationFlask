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

from .autils import SppasFiles
from .infotier import sppasMetaInfoTier
from .log import sppasLog

# ----------------------------------------------------------------------------


MSG_ANN_DISABLED = "Annotation {:s} is disabled due to the following error: {}"
MSG_LOAD_RESOURCES = "Loading resources..."
MSG_GET_FILES = "Create the list of files to be processed."
MSG_NO_FILE = "No file to process."
MSG_ONE_FILE = "One file will be processed."
MSG_N_FILES = "A list of {:d} files will be processed."

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

        # Run all enabled annotations -- store stats on successes
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
                ann_stats[i] = self._run_annotation(annotation_key)
            except Exception as e:
                self._logfile.print_message("{:s}".format(str(e)), indent=1, status=-1)
                logging.info(traceback.format_exc())
                ann_stats[i] = 0

        # Log file & Merge
        self._logfile.print_newline()
        if self.__do_merge:
            self._merge()
        self._logfile.print_separator()
        self._logfile.print_stats(ann_stats)
        self._logfile.close()

        # Clean end
        self._parameters = None
        self._progress = None

    # -----------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------------

    def __get_instance_name(self, annotation_key):
        class_name = None
        for i in range(self._parameters.get_step_numbers()):
            a = self._parameters.get_step(i)
            if a.get_key() == annotation_key:
                class_name = a.get_api()
                break
        if class_name is None:
            raise KeyError('Unknown annotation key: {:s}'.format(annotation_key))

        return getattr(sys.modules[__name__], class_name)

    # ------------------------------------------------------------------------

    def __create_ann_instance(self, annotation_key):
        """Create and configure an instance of an automatic annotation.

        :param annotation_key: (str) Key of an annotation
        :returns: sppasBaseAnnotation

        """
        # Find the index of this annotation
        step_idx = self._parameters.get_step_idx(annotation_key)

        # Create the instance and fix options
        try:
            auto_annot = self.__get_instance_name(annotation_key)(self._logfile)
        except Exception as e:
            self._parameters.disable_step(step_idx)
            self._logfile.print_message(MSG_ANN_DISABLED.format(annotation_key, str(e)))
            return None

        self._fix_ann_options(annotation_key, auto_annot)
        self._fix_ann_extensions(auto_annot)

        # Load language resources
        if self._progress:
            self._progress.set_text(MSG_LOAD_RESOURCES)
        step = self._parameters.get_step(step_idx)
        try:
            auto_annot.load_resources(*step.get_langresource(),
                                      lang=step.get_lang())
        except Exception as e:
            self._parameters.disable_step(step_idx)
            self._logfile.print_message(MSG_ANN_DISABLED.format(annotation_key, str(e)))
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
        for out_format in SppasFiles.OUT_FORMATS:
            # Get the output extension defined in the parameters
            ext = self._parameters.get_output_extension(out_format)
            # Set this output extension to the annotation instance
            auto_annot.set_out_extension(ext, out_format)

    # -----------------------------------------------------------------------

    def _run_annotation(self, annotation_key):
        """The generic solution to run any automatic annotation.

        :param annotation_key: (str) Key of an annotation
        :returns: number of files processed successfully

        """
        # Create the annotation instance
        a = self.__create_ann_instance(annotation_key)
        if a is None:
            self._logfile.print_message("Annotation is un-available. "
                                        "No files processed.", indent=0)
            return 0

        # Fix the list of input files to be processed
        self._logfile.print_message(MSG_GET_FILES, indent=0)
        files_to_process = self.get_annot_files(a)
        if len(files_to_process) == 0:
            self._logfile.print_message(MSG_NO_FILE, indent=1)
        elif len(files_to_process) == 1:
            self._logfile.print_message(MSG_ONE_FILE, indent=1)
        else:
            self._logfile.print_message(MSG_N_FILES.format(len(files_to_process)), indent=1)

        # Run the automatic annotation on all the listed files
        out_files = a.batch_processing(files_to_process, self._progress)

        # Add newly created files to the workspace
        self._parameters.add_to_workspace(out_files)
        return len(out_files)

    # -----------------------------------------------------------------------
    # Manage annotations:
    # -----------------------------------------------------------------------

    def _merge(self):
        """Merge all annotated files."""
        self._logfile.print_separator()
        self._logfile.print_message("Merge files", indent=0)
        self._logfile.print_separator()
        if self._progress:
            self._progress.set_header("Merge annotations in a file")
            self._progress.update(0, "")

        # get the default output extension of any annotation of type ANNOT.
        output_format = SppasFiles.get_default_extension("ANNOT_ANNOT")

        # Get the list of checked roots
        wkp = self._parameters.get_workspace()
        roots = wkp.get_fileroot_from_state(States().CHECKED) + wkp.get_fileroot_from_state(States().AT_LEAST_ONE_CHECKED)
        if len(roots) == 0:
            return
        total = len(roots)

        for i, root in enumerate(roots):
            nb_files = 0
            trs = sppasTranscription()
            self._logfile.print_message("Merge checked files with root: " + root.id, indent=1)
            if self._progress:
                self._progress.set_text(os.path.basename(root.id) + " (" + str(i+1) + "/" + str(total)+")")

            for fn in root:
                if root.pattern(fn.id) == "-merge":
                    continue
                is_expected = False
                for e in SppasFiles.get_informat_extensions("ANNOT_ANNOT"):
                    if fn.get_extension().lower() == e.lower():
                        is_expected = True
                        break
                if is_expected is True:
                    if fn.get_state() == States().CHECKED:
                        nb = self.__add_trs(trs, fn.id)
                        if nb > 0:
                            self._logfile.print_message("[   ADD   ] "+fn.get_name()+" "+fn.get_extension(), indent=2)
                            nb_files += nb
                        else:
                            # An error occurred
                            self._logfile.print_message(fn.get_name()+" "+fn.get_extension(), indent=2, status=-1)
                else:
                    # Ignore this file: not checked
                    self._logfile.print_message(fn.get_name() + " " + fn.get_extension(), indent=2, status=2)

            if nb_files > 1:
                try:
                    # Add the information tier
                    info_tier = sppasMetaInfoTier(trs)
                    tier = info_tier.create_time_tier(trs.get_min_loc().get_midpoint(), trs.get_max_loc().get_midpoint())
                    trs.append(tier)
                    # Save merged file
                    out_file = root.id + "-merge" + output_format
                    parser = sppasTrsRW(out_file)
                    parser.write(trs)
                    self._logfile.print_message(out_file, indent=1, status=0)
                    self._parameters.add_to_workspace([out_file])
                except Exception as e:
                    self._logfile.print_message(str(e), indent=1, status=-1)
            else:
                self._logfile.print_message("Not enough files.", indent=2, status=0)

            if self._progress:
                self._progress.set_fraction(float((i+1))/float(total))
            self._logfile.print_newline()

            # Python should do it
            del trs

        if self._progress:
            self._progress.update(1, "Completed.")
            # self._progress.set_header("")

    # -----------------------------------------------------------------------
    # Manage files:
    # -----------------------------------------------------------------------

    def get_annot_files(self, annotation):
        """Search for files of the workspace to be annotated by the given ann.

        :param annotation: (sppasBaseAnnot) Annotation instance
        :returns: List of file names matching patterns and extensions

        """
        # Get the list of checked roots of the workspace.
        wkp = self._parameters.get_workspace()
        roots = wkp.get_fileroot_from_state(States().CHECKED) + wkp.get_fileroot_from_state(States().AT_LEAST_ONE_CHECKED)
        if len(roots) == 0:
            logging.info("None of the roots is checked in the workspace.")
            return []

        # Get the list of patterns and the list of extensions
        all_patterns = annotation.get_input_patterns()
        all_extensions = annotation.get_input_extensions()

        if isinstance(all_patterns, (list, tuple)) is False:
            raise TypeError("A list of patterns was expected")
        # We should have the same number of patterns than extensions
        if len(all_patterns) != len(all_extensions):
            raise TypeError("List lengths differ: {:d} != {:d}".format(len(all_patterns), len(all_extensions)))

        files = list()
        types = annotation.get_types()
        for root in roots:
            # Search for the files: 0 or 1 for each defined -pattern.extension
            founded_files = self.__search_for_files(root.id, all_patterns, all_extensions)
            if len(founded_files) > 0:
                if len(types) == 0 or "STANDALONE" in types:
                    files.append(founded_files)

                if "SPEAKER" in types:
                    other_files = self.__search_for_other_files(wkp, root, "SPEAKER", all_patterns, all_extensions)
                    for other_root_id in other_files:
                        files.append((founded_files, other_files[other_root_id]))

                if "INTERACTION" in types:
                    other_files = self.__search_for_other_files(wkp, root, "INTERACTION", all_patterns, all_extensions)
                    for other_root_id in other_files:
                        files.append((founded_files, other_files[other_root_id]))

        return files

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

        logging.warning("No file is matching the root {:s} with one of: {}".format(rootname, extensions))
        return None

    # ------------------------------------------------------------------------

    def __search_for_files(self, root_id, all_patterns, all_extensions):
        """Search for the files: 0 or 1 for each defined -pattern.extension."""
        founded_files = list()
        for pattern, extensions in zip(all_patterns, all_extensions):
            # Create a list with the pattern followed by each possible extension
            if len(pattern) > 0:
                # pat_ext = [pattern + self._parameters.get_output_format()]
                pat_ext = list()
                for e in extensions:
                    pat_ext.append(pattern + e)
            else:
                pat_ext = extensions
            new_file = sppasAnnotationsManager._get_filename(root_id, pat_ext)
            if new_file is not None:
                founded_files.append(new_file)
        return founded_files

    # ------------------------------------------------------------------------

    def __search_for_other_files(self, wkp, root, ann_type, all_patterns, all_extensions):
        """Search for the files in the references if SPEAKER/INTERACTIONS."""
        other_files = dict()
        for ref in root.get_references():
            if ref.get_type() == ann_type:
                for fr in wkp.get_fileroot_with_ref(ref):
                    if fr.id != root.id:
                        other_files[fr.id] = self.__search_for_files(fr.id, all_patterns, all_extensions)

        return other_files

    # ------------------------------------------------------------------------

    def __add_trs(self, trs, trs_inputfile):
        """Add content of trs_inputfile to trs."""
        try:
            parser = sppasTrsRW(trs_inputfile)
            trs_input = parser.read(trs_inputfile)
        except Exception:
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
