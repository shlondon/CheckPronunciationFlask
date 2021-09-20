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

    src.ui.phoenix.page_files.filesviewctrl.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import wx
import wx.lib.newevent

from sppas.src.config import paths
from sppas.src.config import sppasTrash
from sppas.src.anndata import sppasTrsRW
from sppas.src.wkps import States, FileName, FileRoot, FilePath, sppasWorkspace
from sppas.src.videodata import video_extensions
from sppas.src.imgdata import image_extensions
from sppas.src.audiodata import audio_extensions

from ..windows import sppasPanel
from ..windows import sppasScrolledPanel
from ..windows import sppasCollapsiblePanel
from ..windows import sppasSimpleText
from ..windows.image import ColorizeImage
from ..windows import sppasListCtrl
from ..tools import sppasSwissKnife
from ..main_events import DataChangedEvent

from .textedit import sppasTextEditDialog, EVT_CLOSE_EDIT

# ---------------------------------------------------------------------------
# Internal use of an event, when an item is clicked.

ItemClickedEvent, EVT_ITEM_CLICKED = wx.lib.newevent.NewEvent()
ItemClickedCommandEvent, EVT_ITEM_CLICKED_COMMAND = wx.lib.newevent.NewCommandEvent()

# ---------------------------------------------------------------------------


STATES_ICON_NAMES = {
    States().MISSING: "choice_checkbox_dashed",
    States().UNUSED: "choice_checkbox",
    States().CHECKED: "choice_checked",
    States().LOCKED: "locked",
    States().AT_LEAST_ONE_CHECKED: "choice_pos",
    States().AT_LEAST_ONE_LOCKED: "choice_neg"
}

# ---------------------------------------------------------------------------


class FileAnnotIcon(object):
    """Represents the link between a file extension and an icon name.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2019  Brigitte Bigi

    All supported file formats of 'anndata' are linked to an icon file.
    All 'wav' files are linked to an icon file.

    """

    def __init__(self):
        """Constructor of a FileAnnotIcon.

        Set the name of the icon for all known extensions of annotations.

        Create a dictionary linking a file extension to the name of the
        software it comes from. It is supposed this name is matching an
        an icon in PNG format.

        """
        self.__exticon = dict()

        # Add multimedia extensions
        for ext in audio_extensions:
            self.__exticon[ext.upper()] = "audio"
        for ext in image_extensions:
            self.__exticon[ext.upper()] = "image"
        for ext in video_extensions:
            self.__exticon[ext.upper()] = "video"

        # Add annotated files extensions
        for ext in sppasTrsRW.TRANSCRIPTION_TYPES:
            software = sppasTrsRW.TRANSCRIPTION_TYPES[ext]().software
            if ext.startswith(".") is False:
                ext = "." + ext
            self.__exticon[ext.upper()] = software

    # -----------------------------------------------------------------------

    def get_icon_name(self, ext):
        """Return the name of the icon matching the given extension.

        A default icon is returned if the extension is unknown.
        It is supposed that the icon is available in the set of icons in
        SPPAS (it is not verified).

        :param ext: (str) An extension of an annotated or an audio file.
        :returns: (str) Name of an icon

        """
        if ext.startswith(".") is False:
            ext = "." + ext
        soft = self.__exticon.get(ext.upper(), "files-unk-file")
        return soft

    # -----------------------------------------------------------------------

    def get_software(self):
        return [self.__exticon[ext] for ext in self.__exticon]

    def get_extensions(self):
        return list(self.__exticon.keys())

    # -----------------------------------------------------------------------

    def get_names(self):
        """Return the list of known icon names."""
        names = list()
        for ext in self.__exticon:
            n = self.get_icon_name(ext)
            if n not in names:
                names.append(n)

        return names

# ---------------------------------------------------------------------------


class FileTreeViewPanel(sppasScrolledPanel):
    """A control to display data files in a tree-spreadsheet style.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2020  Brigitte Bigi

    This class manages a sppasWorkspace() instance to add/remove/delete files and
    the wx objects to display it.

    """
    def __init__(self, parent, name=wx.PanelNameStr):
        """Constructor of the FileTreeView.

        :param parent: (wx.Window)
        :param name: (str)

        """
        super(FileTreeViewPanel, self).__init__(parent, name=name)

        # The workspace to display
        self.__data = sppasWorkspace()

        # Each FilePath has its own CollapsiblePanel in the sizer
        self.__fps = dict()  # key=fp.id, value=FilePathCollapsiblePanel
        self._create_content()
        self._setup_events()

        # Look&feel
        self.SetBackgroundColour(wx.GetApp().settings.bg_color)
        self.SetForegroundColour(wx.GetApp().settings.fg_color)
        self.SetFont(wx.GetApp().settings.text_font)

    # ------------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------------

    def get_data(self):
        """Return the data."""
        return self.__data

    # ------------------------------------------------------------------------

    def set_data(self, data):
        """Set the data and update the corresponding wx objects."""
        self.__data = data
        self.__update()

    # ------------------------------------------------------------------------

    def AddFiles(self, entries):
        """Add a list of files or folders.

        The given entries must include their absolute path.

        :param entries: (list of str) Filename or folder with absolute path.
        :returns: (int) Number of items added in the tree (folders, roots and files)

        """
        modified = 0

        for entry in entries:
            if os.path.isdir(entry):
                m = self.add_folder(entry, add_files=True)
                modified += len(m)

            elif os.path.isfile(entry):
                m = self.add_file(entry)
                modified += len(m)

        if modified > 0:
            self.GetParent().SendSizeEvent()
            # self.Layout()
            # self.Refresh()

        return modified

    # ------------------------------------------------------------------------

    def RemoveCheckedFiles(self):
        """Remove all checked files.

        :returns: (list) List of removed filenames

        """
        removed = list()
        checked_fns = self.__data.get_filename_from_state(States().CHECKED)
        for fn in checked_fns:
            removed_ids = self.__data.remove_file(fn.get_id())
            for fs_id in removed_ids:
                # The path was removed
                if fs_id in self.__fps:
                    self.__remove_folder_panel(fs_id)
                    wx.LogMessage('{:s} removed.'.format(fs_id))
                else:
                    # Either a FileRoot or a FileName.
                    is_root = False
                    fs = self.__data.get_object(fs_id)
                    if isinstance(fs, FileRoot):
                        is_root = True
                    # Get its path first!
                    fp_id = FilePath(os.path.dirname(fs_id)).get_id()
                    if fp_id in self.__fps:
                        p = self.__fps[fp_id]
                        r = p.remove_root(fs_id)
                        if r is False:
                            r = p.remove(fs_id)
                            removed.append(fs_id)
                        # OK. The FileName or FileRoot was removed...
                        if r is True:
                            wx.LogMessage('{:s} removed.'.format(fs_id))
                            # Update the state of the path.
                            fp = self.__data.get_object(fp_id)
                            if fp is not None:
                                p.change_state(fp_id, fp.get_state())
                                # Update the state of the root (fs was a FileName)
                                if is_root is False:
                                    # (if the root was not removed)
                                    fr = self.__data.get_object(FileRoot.root(fs_id))
                                    if fr is not None:
                                        p.change_state(fr.get_id(), fr.get_state())

        if len(removed) > 0:
            # self.Layout()
            # self.Refresh()
            self.GetParent().SendSizeEvent()

        return removed

    # ------------------------------------------------------------------------

    def DeleteCheckedFiles(self):
        """Delete all checked files."""
        removed_filenames = self.RemoveCheckedFiles()

        # move the files into the trash of SPPAS
        for filename in removed_filenames:
            try:
                sppasTrash().put_file_into(filename)
                wx.LogMessage('{:s} moved into SPPAS Trash.'.format(filename))
            except Exception as e:
                # Re-Add it into the data and the panels or not?????
                wx.LogError("File {!s:s} can't be deleted due to the "
                            "following error: {:s}.".format(filename, str(e)))

    # ------------------------------------------------------------------------

    def EditCheckedFiles(self):
        """Edit all checked files in a text editor."""
        checked_fn = self.GetCheckedFiles()
        checked_files = [fn.id for fn in checked_fn]

        editor = sppasTextEditDialog(self, checked_files)
        nb_loaded = 0
        for fn, filename in zip(checked_fn, checked_files):
            if editor.is_loaded(filename) is True:
                nb_loaded += 1
                self.change_state(fn, States().LOCKED)

        if nb_loaded > 0:
            self.Notify()

        editor.Show()

    # ------------------------------------------------------------------------

    def GetCheckedFiles(self):
        """Return the list of checked files.

        :returns: List of FileName

        """
        return self.__data.get_filename_from_state(States().CHECKED)

    # ------------------------------------------------------------------------

    def Check(self, entries):
        """Check a list of entries.

        Entries are a list of filenames with absolute path or FileName
        instances or both.

        :param entries: (list) identifiers of objects or objects in data

        """
        for entry in entries:
            self.change_state(entry, States().CHECKED)

    # ------------------------------------------------------------------------

    def Lock(self, entries):
        """Lock a list of entries.

        Entries are a list of either folder name, file name with absolute path
        or FileName, FileRoot or FilePath or any of them.

        :param entries: (list) identifiers of objects or objects in data

        """
        for entry in entries:
            self.change_state(entry, States().LOCKED)

    # ------------------------------------------------------------------------
    # Manage the data and their panels
    # ------------------------------------------------------------------------

    def add_folder(self, foldername, add_files=True):
        """Add a folder and its files into to the data and display it.

        Do not layout/refresh the panel.

        :param foldername: (str) Absolute path
        :param add_files: (bool) Add also the files of this folder
        :return: list of added items

        """
        if foldername.endswith(".."):
            wx.LogError('Adding the parent folder is forbidden: {}'.format(str(foldername)))
            return list()

        wx.LogMessage('Add folder: {:s}'.format(str(foldername)))
        added = list()

        # Get or create the FilePath of the foldername
        try:
            fp = FilePath(foldername)
        except Exception as e:
            wx.LogError("{:s}".format(str(e)))
            return added

        fpx = self.__data.get_object(fp.id)
        if fpx is None:
            self.__data.add(fp)
            self.__add_folder_panel(fp)
            added.append(foldername)

        if add_files is True:
            # add all files of this folder into the FilePath and the panel
            for f in sorted(os.listdir(foldername)):
                fullname = os.path.join(foldername, f)
                if os.path.isfile(fullname):
                    m = self.add_file(fullname)
                    if len(m) > 0:
                        added.extend(m)

        return added

    # ------------------------------------------------------------------------

    def add_file(self, filename):
        """Add a file to the data and into a path-root panel.

        Do not layout/refresh the panel.

        :param filename: (str) Absolute name of a file
        :return: (list)

        """
        wx.LogMessage('Add file: {:s}'.format(str(filename)))
        added = list()

        # get the FilePath of this filename
        fpx = FilePath(os.path.dirname(filename))
        fp = self.__data.get_object(fpx.get_id())
        if fp is None:
            added = self.add_folder(fpx.get_id(), add_files=False)
            if len(added) == 0:
                wx.LogError("Folder not added: {:s}".format(fpx.get_id()))
                return list()
            fp = self.__data.get_object(fpx.get_id())
            if fp is None:
                wx.LogError("Folder not added: {:s}".format(fpx.get_id()))
                return list()

        # get the panel of this fp
        p = self.__fps[fp.get_id()]

        # add the entry into the data
        added_fs = self.__data.add_file(filename, brothers=False, ctime=0.)
        if len(added_fs) == 0:
            wx.LogWarning("File not added: {:s}".format(filename))
            return added

        # add the entries into the panels
        for fs in added_fs:
            if isinstance(fs, FileName):
                wx.LogDebug("Added file to the data {:s}".format(fs.get_id()))
                fr = self.__data.get_object(FileRoot.root(fs.get_id()))
                p.add_file(fr, fs)
                added.append(fs)

        return added

    # ------------------------------------------------------------------------

    def change_state(self, entry, state):
        """Change the state of an entry.

        Entry is either a folder name, a file name with absolute path
        or a FileName, a FileRoot or a FilePath.
        If entry is already locked, this will have no effect.

        :param entry: (str/FileName/FileRoot/FilePath)
        :param state: (States/int)

        """
        if isinstance(entry, (FileName, FileRoot, FilePath)) is False:
            fs = self.__data.get_object(entry)
            if fs is None:
                wx.LogWarning("Wrong entry name to change state: {:s}".format(entry))
                return
        else:
            fs = entry

        modified = self.__data.set_object_state(state, fs)
        for fs in modified:
            wx.LogMessage("{:s} state changed to {:d}".format(fs.get_id(), state))
            # Update object in the panel
            panel = self.__get_path_panel(fs)
            if panel is not None:
                panel.change_state(fs.get_id(), fs.get_state())

    # ------------------------------------------------------------------------

    def __add_folder_panel(self, fp, idx=-1):
        """Create a child panel to display the content of a FilePath.

        :param fp: (FilePath)
        :param idx: Insert panel at given index. Use -1 to append the panel.
        :return: FilePathCollapsiblePanel

        """
        p = FilePathCollapsiblePanel(self, fp)
        p.SetFocus()
        self.ScrollChildIntoView(p)
        p.GetPane().Bind(EVT_ITEM_CLICKED, self._process_item_clicked)

        if idx == -1:
            self.GetSizer().Add(p, 0, wx.EXPAND | wx.ALL, border=sppasPanel.fix_size(6))
        else:
            self.GetSizer().Insert(idx, p, 0, wx.EXPAND | wx.ALL, border=sppasPanel.fix_size(6))

        self.__fps[fp.get_id()] = p
        return p

    # ------------------------------------------------------------------------

    def __remove_folder_panel(self, identifier):
        """Remove a child panel that displays the content of a FilePath.

        :param identifier: (str)
        :return: FilePathCollapsiblePanel

        """
        if identifier in self.__fps:
            path_panel = self.__fps[identifier]
            path_panel.Destroy()
            del self.__fps[identifier]

    # ------------------------------------------------------------------------

    def __update(self):
        """Update the currently displayed wx objects to match the data.

        """
        # Remove paths of the panel if not in the data
        rm_fpid = list()
        for fpid in self.__fps:
            if fpid not in self.__data:
                rm_fpid.append(fpid)
        for fpid in reversed(rm_fpid):
            self.__remove_folder_panel(fpid)

        # Add or update
        for i, fp in enumerate(self.__data.get_paths()):
            if fp.get_id() not in self.__fps:
                p = self.__add_folder_panel(fp, i)
                p.update(fp)
            else:
                self.__fps[fp.get_id()].update(fp)

        self.GetParent().SendSizeEvent()

    # ------------------------------------------------------------------------

    def _create_content(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.Layout()
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.SetAutoLayout(True)

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def Notify(self):
        evt = DataChangedEvent()
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # ------------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # The user pressed a key of its keyboard
        # self.Bind(wx.EVT_KEY_DOWN, self._process_key_event)

        # The user clicked an item
        self.Bind(EVT_ITEM_CLICKED, self._process_item_clicked)

        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapseChanged)
        self.Bind(EVT_CLOSE_EDIT, self._process_editor_closed)

    # ------------------------------------------------------------------------

    def _process_item_clicked(self, event):
        """Process an action event: an item was clicked.

        The sender of the event is either a Path or a Root Collapsible Panel.

        :param event: (wx.Event)

        """
        # the object is a FileBase (path, root or file)
        object_id = event.id
        filebase = self.__data.get_object(object_id)
        if filebase is None:
            # it happens when the graphical object is created but it does not
            # correspond to a valid instance of a file/folder
            wx.LogWarning("The id {:s} does not match a valid file/folder.")
            return

        # change state of the item
        current_state = filebase.get_state()
        new_state = States().UNUSED
        if current_state == States().UNUSED:
            new_state = States().CHECKED
        modified = self.__data.set_object_state(new_state, filebase)

        # update the corresponding panel(s)
        if len(modified) > 0:
            self.Notify()
            for fs in modified:
                panel = self.__get_path_panel(fs)
                if panel is not None:
                    panel.change_state(fs.get_id(), fs.get_state())

    # ------------------------------------------------------------------------

    def _process_editor_closed(self, event):
        """Process an event: the editor dialog was closed.

        :param event: (wx.Event)

        """
        filenames = event.files
        if isinstance(filenames, (list, tuple)) is False:
            filenames = [filenames]

        for filename in filenames:
            filebase = self.__data.get_object(filename)
            cur_state = filebase.get_state()
            if cur_state == States().LOCKED:
                self.change_state(filebase, States().CHECKED)

        self.Notify()
        textedit = event.GetEventObject()
        if textedit:
            textedit.Destroy()

    # ------------------------------------------------------------------------

    def __get_path_panel(self, fs):
        """Return the collapsible panel of the given FileXXXX."""
        if isinstance(fs, FilePath):
            fp = fs
        elif isinstance(fs, FileRoot):
            fp = self.__data.get_parent(fs)
        elif isinstance(fs, FileName):
            fr = self.__data.get_parent(fs)
            fp = self.__data.get_parent(fr)
        else:
            return None

        if fp.get_id() not in self.__fps:
            wx.LogError("The entry {} of type {} has no parent panel.".format(fs, type(fs)))
            return None

        return self.__fps[fp.get_id()]

    # ------------------------------------------------------------------------

    def OnCollapseChanged(self, evt=None):
        """One of the paths was collapsed/expanded."""
        panel = evt.GetEventObject()
        fs_id = panel.get_id()
        fs = self.__data.get_object(fs_id)
        if fs is None:
            return
        if fs.subjoined is None:
            fs.subjoined = dict()
        fs.subjoined['expand'] = panel.IsExpanded()

        if isinstance(fs, FilePath):
            self.Notify()

            # Required for the parent to do properly its layout:
            # (i.e. estimate the height needed by each panel and refresh)
            self.SendSizeEventToParent()

        self.ScrollChildIntoView(panel)

    # ------------------------------------------------------------------------

    def OnSize(self, event):
        """Handle the wx.EVT_SIZE event.

        :param event: a SizeEvent event to be processed.

        """
        # each time our size is changed, the child panel needs a resize.
        self.Layout()

# ---------------------------------------------------------------------------


class FilePathCollapsiblePanel(sppasCollapsiblePanel):
    """A panel to display the fp as a list of fr.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2019  Brigitte Bigi

    """

    def __init__(self, parent, fp, name="fp-panel"):
        super(FilePathCollapsiblePanel, self).__init__(parent, label=fp.get_id(), name=name)

        self._create_content(fp)
        self._setup_events()

        # Each FileRoot has its own CollapsiblePanel in the sizer
        self.__fpid = fp.get_id()
        self.__frs = dict()  # key=root.id, value=FileRootCollapsiblePanel

        # Look&feel
        try:
            self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
            self.SetForegroundColour(wx.GetApp().settings.fg_color)
            self.SetFont(wx.GetApp().settings.text_font)
        except AttributeError:
            self.InheritAttributes()

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, color):
        """Calculate a lightness or darkness background color."""
        r, g, b = color.Red(), color.Green(), color.Blue()
        delta = 5
        if (r + g + b) > 384:
            color = wx.Colour(r, g, b, 50).ChangeLightness(100 - delta)
        else:
            color = wx.Colour(r, g, b, 50).ChangeLightness(100 + delta)

        wx.Window.SetBackgroundColour(self, color)
        for c in self.GetChildren():
            c.SetBackgroundColour(color)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        f = wx.Font(font.GetPointSize(),
                    font.GetFamily(),
                    font.GetStyle(),
                    wx.FONTWEIGHT_BOLD,
                    font.GetUnderlined(),
                    font.GetFaceName())
        sppasCollapsiblePanel.SetFont(self, f)
        self.GetPane().SetFont(font)
        self.Layout()

    # ----------------------------------------------------------------------

    def get_id(self):
        """Return the identifier of the path this panel is displaying."""
        return self.__fpid

    # ----------------------------------------------------------------------

    def add_file(self, fr, fn):
        """Add a file in the appropriate root of the child panel.

        """
        if fr.get_id() not in self.__frs:
            p = self.__add_root_panel(fr)
        else:
            p = self.__frs[fr.get_id()]

        added = p.add(fn)
        self.Layout()
        # self.Refresh()
        return added

    # ----------------------------------------------------------------------

    def remove(self, identifier):
        """Remove a file or a root of the panel.

        """
        if identifier in self.__frs:
            self.__remove_root(identifier)
            return True
        else:
            fr_id = FileRoot.root(identifier)
            if fr_id in self.__frs:
                p = self.__frs[fr_id]
                removed = p.remove(identifier)
                if removed is True:
                    self.Layout()
                    return True

        return False

    # ----------------------------------------------------------------------

    def remove_file(self, fr_id, fn_id):
        """Remove a file of the appropriate root of the child panel.

        """
        removed = False
        if fr_id in self.__frs:
            p = self.__frs[fr_id]
            removed = p.remove(fn_id)
            if removed is True:
                self.Layout()

        return removed

    # ----------------------------------------------------------------------

    def add_root(self, fr, idx=-1):
        """Add a new root panel.

        """
        added = False
        if fr.get_id() not in self.__frs:
            p = self.__add_root_panel(fr, idx)
            added = True
            for fn in fr:
                p.add(fn)

        return added

    # ----------------------------------------------------------------------

    def remove_root(self, fr_id):
        """Remove a full root of the child panel.

        """
        if fr_id not in self.__frs:
            return False
        self.__remove_root(fr_id)
        return True

    # ------------------------------------------------------------------------

    def change_state(self, identifier, state):
        icon_name = STATES_ICON_NAMES[state]

        if self.__fpid == identifier:
            btn = self.FindButton("choice_checkbox")
            btn.SetImage(icon_name)
            btn.Refresh()

        elif identifier in self.__frs:
            self.__frs[identifier].change_state(identifier, state)

        else:
            frid = FileRoot.root(identifier)
            if frid in self.__frs:
                self.__frs[frid].change_state(identifier, state)

    # ------------------------------------------------------------------------

    def update(self, fs):
        """Update the given file structure.

        :param fs: (FilePath/FileRoot/FileName)

        """
        if isinstance(fs, FilePath):
            if fs.get_id() == self.__fpid:
                # Update the state
                self.change_state(self.__fpid, fs.get_state())
                # Remove roots of the panel if not in the data
                rm_frid = list()
                for frid in self.__frs:
                    if frid not in fs:
                        rm_frid.append(frid)
                for frid in reversed(rm_frid):
                    self.__remove_root(frid)

                # Add or update the roots
                for i, fr in enumerate(fs):
                    if fr.get_id() not in self.__frs:
                        self.add_root(fr, i)
                    else:
                        self.__frs[fr.get_id()].update(fr)

                self._update_expander(fs)
            else:
                return

        elif isinstance(fs, FileRoot):
            if fs.get_id() in self.__frs:
                p = self.__frs[fs.get_id()]
                p.update(fs)

        elif isinstance(fs, FileName):
            frid = FileRoot.root(fs.get_id())
            if frid in self.__frs:
                p = self.__frs[frid]
                p.update(fs)

        self.Layout()
        self.Refresh()

    # ------------------------------------------------------------------------

    def __add_root_panel(self, fr, idx=-1):
        """Create a child panel to display the content of a FileRoot.

        :param fr: (FileRoot)
        :return: FileRootCollapsiblePanel

        """
        p = FileRootCollapsiblePanel(self.GetPane(), fr)
        p.SetFocus()
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapseChanged, p)
        sizer = self.GetPane().GetSizer()
        if idx == -1:
            sizer.Add(p, 0, wx.EXPAND | wx.ALL, border=sppasPanel.fix_size(4))
        else:
            sizer.Insert(idx, p, 0, wx.EXPAND | wx.ALL, border=sppasPanel.fix_size(4))
        self.__frs[fr.get_id()] = p
        return p

    # ------------------------------------------------------------------------

    def __remove_root(self, identifier):
        p = self.__frs[identifier]
        p.Destroy()
        del self.__frs[identifier]
        self.Layout()
        self.Refresh()

    # ------------------------------------------------------------------------
    # Manage the content
    # ------------------------------------------------------------------------

    def _create_content(self, fp):
        self._update_expander(fp)
        self.AddButton("folder")
        self.AddButton("choice_checkbox")

    # -----------------------------------------------------------------------

    def _update_expander(self, fp):
        expand = True
        if fp.subjoined is not None:
            if "expand" in fp.subjoined:
                expand = fp.subjoined["expand"]

        if expand is True:
            self.Expand()
        else:
            self.Collapse()

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def notify(self, identifier):
        """The parent has to be informed of a change of content."""
        evt = ItemClickedEvent(id=identifier)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # ------------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        self.FindButton("choice_checkbox").Bind(wx.EVT_BUTTON, self.OnCkeckedPath)

    # ------------------------------------------------------------------------

    def OnCollapseChanged(self, evt):
        """One of the roots was collapsed/expanded."""
        panel = evt.GetEventObject()
        self.Layout()
        wx.PostEvent(self.GetParent(), evt)

        # Required for the parent to do properly its layout:
        self.GetParent().SendSizeEvent()

    # ------------------------------------------------------------------------

    def OnCkeckedPath(self, evt):
        self.notify(self.__fpid)

# ---------------------------------------------------------------------------


class FileRootCollapsiblePanel(sppasCollapsiblePanel):
    """A panel to display the fr as a list of fn.

    :author:       Brigitte Bigi
    :organization: Laboratoire Parole et Langage, Aix-en-Provence, France
    :contact:      contact@sppas.org
    :license:      GPL, v3
    :copyright:    Copyright (C) 2011-2019  Brigitte Bigi

    """

    COLUMNS = ['state', 'icon', 'file', 'type', 'date', 'size']

    def __init__(self, parent, fr, name="fr-panel"):
        super(FileRootCollapsiblePanel, self).__init__(
            parent, label=fr.get_id(), name=name)

        self.__ils = list()
        self._create_content(fr)
        self._setup_events()

        # Files are displayed in a listctrl. For convenience, their ids are
        # stored into a list.
        self.__frid = fr.get_id()
        self.__fns = list()

        # Look&feel
        try:
            self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
            self.SetForegroundColour(wx.GetApp().settings.fg_color)
            self.SetFont(wx.GetApp().settings.text_font)
        except AttributeError:
            self.InheritAttributes()

        # Fill in the controls with the data
        self.update(fr)

    # -----------------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------------

    def SetForegroundColour(self, color):
        """Override."""
        refsctrl = self.FindWindow("textctrl_refs")
        wx.Window.SetForegroundColour(self, color)
        for c in self.GetChildren():
            if c != refsctrl:
                c.SetForegroundColour(color)
        refsctrl.SetForegroundColour(wx.Colour(128, 128, 250, 196))
        self.__il = self.__create_image_list()
        self.FindWindow("listctrl_files").SetImageList(self.__il, wx.IMAGE_LIST_SMALL)

    # -----------------------------------------------------------------------

    def SetBackgroundColour(self, color):
        """Calculate a lightness or darkness background color."""
        r, g, b = color.Red(), color.Green(), color.Blue()
        delta = 10
        if (r + g + b) > 384:
            color = wx.Colour(r, g, b, 50).ChangeLightness(100 - delta)
        else:
            color = wx.Colour(r, g, b, 50).ChangeLightness(100 + delta)

        wx.Window.SetBackgroundColour(self, color)
        for c in self.GetChildren():
            c.SetBackgroundColour(color)

    # -----------------------------------------------------------------------

    def SetFont(self, font):
        """Override."""
        f = wx.Font(font.GetPointSize(),
                    font.GetFamily(),
                    wx.FONTSTYLE_ITALIC,
                    wx.FONTWEIGHT_NORMAL,
                    font.GetUnderlined(),
                    font.GetFaceName())
        sppasCollapsiblePanel.SetFont(self, f)
        self.GetPane().SetFont(font)

        # The change of font implies to re-draw all proportional objects
        self.__il = self.__create_image_list()
        self.FindWindow("listctrl_files").SetImageList(self.__il, wx.IMAGE_LIST_SMALL)
        self.__set_pane_size()
        self.Layout()

    # ----------------------------------------------------------------------

    def get_id(self):
        """Return the identifier of the root this panel is displaying."""
        return self.__frid

    # ----------------------------------------------------------------------

    def add(self, fn, idx=-1):
        """Add a file in the listctrl child panel.

        :param fn: (FileName)
        :param idx: Index to insert the file. Use -1 to append.

        """
        if fn.get_id() in self.__fns:
            return False

        self.__add_file(fn, idx)
        return True

    # ----------------------------------------------------------------------

    def remove(self, identifier):
        """Remove a file of the listctrl child panel.

        :param identifier: (str)
        :return: (bool)

        """
        if identifier not in self.__fns:
            return False

        self.__remove_file(identifier)
        return True

    # ------------------------------------------------------------------------

    def change_state(self, identifier, state):
        """Update the state of the given identifier.

        :param identifier: (str)
        :param state: (State/int)

        """
        icon_name = STATES_ICON_NAMES[state]

        if self.__frid == identifier:
            self.FindButton("choice_checkbox").SetImage(icon_name)
            self.FindButton("choice_checkbox").Refresh()

        else:
            listctrl = self.FindWindow("listctrl_files")
            idx = self.__fns.index(identifier)
            listctrl.SetItem(idx, 0, "", imageId=self.__ils.index(icon_name))

    # ------------------------------------------------------------------------

    def set_refs(self, refs_list):
        """Display the given list of references.

        :param refs_list: (list of sppasCatReference)

        """
        refstext = self.FindWindow("textctrl_refs")
        # convert the list of sppasCatReference instances into a string
        refs_ids = [ref.id for ref in refs_list]
        txt = " ".join(sorted(refs_ids))
        if len(txt) > 0:
            refstext.SetValue(txt)
            refstext.Show()
        else:
            refstext.Hide()

    # ------------------------------------------------------------------------

    def update(self, fs):
        """Update each fn of a given fr or update the given fn.

        :param fs: (FileRoot or FileName)

        """
        if isinstance(fs, FileRoot):
            if fs.get_id() != self.__frid:
                return

            # Remove files of the panel if not in the data
            rm_fnid = list()
            for fnid in self.__fns:
                if fnid not in fs:
                    rm_fnid.append(fnid)
            for fnid in reversed(rm_fnid):
                self.__remove_file(fnid)

            # Update existing files and add if missing
            for i, fn in enumerate(fs):
                if fn.get_id() not in self.__fns:
                    self.add(fn, i)
                else:
                    self.change_state(fn.get_id(), fn.get_state())
                    self.__update_file(fn)

            self.set_refs(fs.get_references())
            self.change_state(fs.get_id(), fs.get_state())
            self._update_expander(fs)

        elif isinstance(fs, FileName):
            self.change_state(fs.get_id(), fs.get_state())
            self.__update_file(fs)

        self.Layout()

    # ------------------------------------------------------------------------
    # Construct the GUI
    # ------------------------------------------------------------------------

    def _create_content(self, fr):
        child_panel = sppasPanel(self)
        child_sizer = wx.BoxSizer(wx.VERTICAL)
        refs_text = self.__create_refstext(child_panel)
        list_ctrl = self.__create_listctrl(child_panel)
        child_sizer.Add(refs_text, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 2)
        child_sizer.Add(list_ctrl, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 2)
        child_panel.SetSizer(child_sizer)
        self.SetPane(child_panel)

        self._update_expander(fr)
        self.AddButton("root")
        self.AddButton("choice_checkbox")

    @property
    def _listctrl(self):
        return self.FindWindow("listctrl_files")

    # ------------------------------------------------------------------------

    def _update_expander(self, fr):
        expand = False
        if fr.subjoined is not None:
            if "expand" in fr.subjoined:
                expand = fr.subjoined["expand"]

        if expand is True:
            self.Expand()
        else:
            self.Collapse()

    # ------------------------------------------------------------------------

    def __create_refstext(self, parent):
        """Create a text control to display references of the root."""
        refs_text = sppasSimpleText(parent, "", name="textctrl_refs")
        refs_text.SetMinSize(wx.Size(-1, self.get_font_height()*2))
        refs_text.Hide()
        return refs_text

    # ------------------------------------------------------------------------

    def __create_listctrl(self, parent):
        """Create a listctrl to display file names and properties."""
        style = wx.BORDER_NONE | wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL  # | wx.LC_HRULES
        lst = sppasListCtrl(parent, style=style, name="listctrl_files")
        lst.SetAlternateRowColour(False)

        info = wx.ListItem()
        info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.Image = -1
        info.Align = 0
        lst.InsertColumn(0, info)
        lst.SetColumnWidth(0, sppasScrolledPanel.fix_size(24))
        lst.AppendColumn("icon",
                         format=wx.LIST_FORMAT_CENTRE,
                         width=sppasScrolledPanel.fix_size(32))
        lst.AppendColumn("file",
                         format=wx.LIST_FORMAT_LEFT,
                         width=sppasScrolledPanel.fix_size(120))
        lst.AppendColumn("type",
                         format=wx.LIST_FORMAT_LEFT,
                         width=sppasScrolledPanel.fix_size(80))
        lst.AppendColumn("date",
                         format=wx.LIST_FORMAT_CENTRE,
                         width=sppasScrolledPanel.fix_size(100))
        lst.AppendColumn("size",
                         format=wx.LIST_FORMAT_RIGHT,
                         width=sppasScrolledPanel.fix_size(60))

        return lst

    # ------------------------------------------------------------------------

    def __create_image_list(self):
        """Create a list of images to be displayed in the listctrl.

        :return: (wx.ImageList)

        """
        icon_size = int(float(self.get_font_height()) * 1.4)

        il = wx.ImageList(icon_size, icon_size)
        self.__ils = list()

        # All icons to represent the state of the root or a filename
        for state in STATES_ICON_NAMES:
            icon_name = STATES_ICON_NAMES[state]
            bitmap = sppasSwissKnife.get_bmp_icon(icon_name, icon_size)
            img = bitmap.ConvertToImage()
            ColorizeImage(img, wx.BLACK, self.GetForegroundColour())
            il.Add(wx.Bitmap(img))
            self.__ils.append(icon_name)

        # The default icon to represent a missing (known) file
        bitmap = sppasSwissKnife.get_bmp_icon("files-file", icon_size)
        il.Add(bitmap)
        self.__ils.append("files-file")

        # The default icon to represent an unknown file
        bitmap = sppasSwissKnife.get_bmp_icon("files-unk-file", icon_size)
        il.Add(bitmap)
        self.__ils.append("files-unk-file")

        # The icons of the known file extensions
        for icon_name in FileAnnotIcon().get_names():
            bitmap = sppasSwissKnife.get_bmp_icon(icon_name, icon_size, "files-file")
            il.Add(bitmap)
            self.__ils.append(icon_name)

        return il

    # ------------------------------------------------------------------------

    def __set_pane_size(self):
        """Fix the size of the child panel."""
        # The listctrl can have an horizontal scrollbar
        bar = 14

        n = self._listctrl.GetItemCount()
        h = int(self.GetFont().GetPixelSize()[1] * 2.)
        self._listctrl.SetMinSize(wx.Size(-1, (n * h) + bar))
        self._listctrl.SetMaxSize(wx.Size(-1, (n * h) + bar + 2))

    # ------------------------------------------------------------------------
    # Management the list of files
    # ------------------------------------------------------------------------

    def __add_file(self, fn, idx=-1):
        """Append a file.

        :param fn: (FileName)

        """
        state_icon_name = STATES_ICON_NAMES[fn.get_state()]
        state_icon_index = self.__ils.index(state_icon_name)
        extension_icon_name = FileAnnotIcon().get_icon_name(fn.get_extension())
        extension_img_index = self.__ils.index(extension_icon_name)

        if idx == -1:
            idx = self._listctrl.GetItemCount()
        index = self._listctrl.InsertItem(idx, state_icon_index)
        self.__fns.append(fn.get_id())

        self._listctrl.SetItemColumnImage(
            index,
            FileRootCollapsiblePanel.COLUMNS.index("icon"),
            extension_img_index)
        self.__update_file(fn)
        self.__set_pane_size()
        self.Layout()

    # ------------------------------------------------------------------------

    def __remove_file(self, identifier):
        """Remove a filename."""
        idx = self.__fns.index(identifier)
        # item = listctrl.GetItem(idx)
        self._listctrl.DeleteItem(idx)

        self.__fns.pop(idx)
        self.__set_pane_size()
        self.Layout()

    # ------------------------------------------------------------------------

    def __update_file(self, fn):
        """Update information of a file, except its icon and its state."""
        if fn.get_id() in self.__fns:
            index = self.__fns.index(fn.get_id())
            self._listctrl.SetItem(index, FileRootCollapsiblePanel.COLUMNS.index("file"), fn.get_name())
            self._listctrl.SetItem(index, FileRootCollapsiblePanel.COLUMNS.index("type"), fn.get_extension())
            self._listctrl.SetItem(index, FileRootCollapsiblePanel.COLUMNS.index("date"), fn.get_date())
            self._listctrl.SetItem(index, FileRootCollapsiblePanel.COLUMNS.index("size"), fn.get_size())
            self._listctrl.RefreshItem(index)

        # update a column size to ensure the filename is fully visible
        fn_chars = 0
        for filename in self.__fns:
            fn = FileName(filename)
            fn_nbc = len(fn.get_name())
            if fn_nbc > fn_chars:
                fn_chars = fn_nbc
        f = self.GetFont().GetPixelSize()[0]
        self._listctrl.SetColumnWidth(2, max(sppasScrolledPanel.fix_size(120), (fn_chars+2)*f))
        self._listctrl.Refresh()

    # ------------------------------------------------------------------------
    # Management of the events
    # ------------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        self.FindButton("choice_checkbox").Bind(wx.EVT_BUTTON, self.OnCkeckedRoot)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__item_selected)

    # ------------------------------------------------------------------------

    def notify(self, identifier):
        """The parent has to be informed of a change of content."""
        evt = ItemClickedEvent(id=identifier)
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

    # ------------------------------------------------------------------------

    def __item_selected(self, event):
        index = self._listctrl.GetFirstSelected()
        self._listctrl.Select(index, on=False)

        # notify parent to decide what has to be done
        self.notify(self.__fns[index])

    # ------------------------------------------------------------------------

    def OnCkeckedRoot(self, evt):
        self.notify(self.__frid)

# ----------------------------------------------------------------------------


class TestPanel(FileTreeViewPanel):

    def __init__(self, parent):
        super(TestPanel, self).__init__(parent, "Files tree view")

        self.AddFiles([os.path.abspath(__file__)])
        self.AddFiles([os.path.join(paths.samples, "samples-fra")])

        self.Check([os.path.join(paths.samples, "samples-fra", "F_F_B003-P9")])
        self.Check([os.path.join(paths.samples, "samples-fra", ".DS_Store")])
        # self.Check([os.path.abspath(__file__)])

        self.Lock([os.path.join(paths.samples, "samples-fra", "F_F_C006-P6.wav")])

        self.RemoveCheckedFiles()
        #self.DeleteCheckedFiles()

