# -*- coding : UTF-8 -*-
"""
:filename: sppas.src.ui.phoenix.page_annotate.annotbook.py
:author:   Brigitte Bigi
:contact:  develop@sppas.org
:summary:  The GUI main annotation page: a notebook.

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
import wx

from sppas.src.config import annots
from sppas.src.config import sppasTypeError
from sppas.src.annotations import sppasParam
from sppas.src.wkps import sppasWorkspace

from ..windows.book import sppasSimplebook
from ..main_events import DataChangedEvent, EVT_DATA_CHANGED

from .annotevent import EVT_ANNOT_PAGE_CHANGE
from .annotselect import sppasAnnotationsPanel
from .annotaction import sppasActionAnnotatePanel
from .annotlog import sppasLogAnnotatePanel

# ---------------------------------------------------------------------------


class sppasAnnotateBook(sppasSimplebook):
    """Create a book to annotate automatically the selected files.

    There's no event for the change of param: the params of the current page
    are set to the other ones when "show_page()" is called.

    It's content is organized with a wxSimpleBook() with:
        - a page to fix parameters then run, then save the report,
        - 3 pages with the lists of annotations to select and configure,
        - a page with the progress bar and the procedure outcome report.

    """

    def __init__(self, parent):
        super(sppasAnnotateBook, self).__init__(
            parent=parent,
            name="annotate_book",
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS
        )
        self.SetEffectsTimeouts(150, 150)

        # The annotations the system can perform
        self.__param = sppasParam()
        self.__pages_annot = dict()

        # 1st page: the buttons to perform actions
        self.ShowNewPage(sppasActionAnnotatePanel(self, self.__param))

        # list of "ann_types" annotations
        for ann_type in annots.types:
            page = sppasAnnotationsPanel(self, self.__param, ann_type)
            self.AddPage(page, text="")
            self.__pages_annot[ann_type] = page

        # 5th page: procedure outcome report
        page = sppasLogAnnotatePanel(self, self.__param)
        self.AddPage(page, text="")

        self._setup_events()

    # ------------------------------------------------------------------------
    # Public methods to access the data
    # ------------------------------------------------------------------------

    def get_data(self):
        """Return the data currently displayed.

        :returns: (sppasWorkspace) The workspace with files to annotate/annotated

        """
        return self.__param.get_workspace()

    # ------------------------------------------------------------------------

    def set_data(self, data):
        """Assign new data to this page.

        :param data: (sppasWorkspace) The workspace with files to annotate/annotated

        """
        if isinstance(data, sppasWorkspace) is False:
            raise sppasTypeError("sppasWorkspace", type(data))

        self.__param.set_workspace(data)
        self.__send_data(self.GetParent())

    # -----------------------------------------------------------------------
    # Events management
    # -----------------------------------------------------------------------

    def _setup_events(self):
        """Associate a handler function with the events.

        It means that when an event occurs then the process handler function
        will be called.

        """
        # The data have changed.
        # This event is sent by any of the children
        self.Bind(EVT_DATA_CHANGED, self._process_data_changed)

        # Change the displayed page
        self.Bind(EVT_ANNOT_PAGE_CHANGE, self._process_page_change)

    # ------------------------------------------------------------------------

    def _process_page_change(self, event):
        """Process a PageChangeEvent.

        :param event: (wx.Event)

        """
        try:
            destination = event.GetToPage()
            fct = event.GetFctName()
            args = event.GetFctArgs()
        except AttributeError:
            destination = "page_annot_actions"
            fct = ""
            args = None

        self.show_page(destination, fct, args)

    # -----------------------------------------------------------------------

    def _process_data_changed(self, event):
        """Process a change of data.

        Set the data of the event to the other panels.

        :param event: (wx.Event)

        """
        emitted = event.GetEventObject()
        try:
            wkp = event.data
        except AttributeError:
            wx.LogError('Data were not sent in the event emitted by {:s}'
                        '.'.format(emitted.GetName()))
            return
        self.__param.set_workspace(wkp)
        self.__send_data(emitted)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __send_data(self, emitted):
        """Set a change of data to the children, send to the parent.

        :param emitted: (wx.Window) The panel the data are coming from

        """
        # Set the data to appropriate children panels
        for panel in self.GetChildren():
            if emitted != panel:
                try:
                    panel.set_param(self.__param)
                except:
                    pass

        # Send the data to the parent
        pm = self.GetParent()
        if pm is not None and emitted != pm:
            data = self.__param.get_workspace()
            evt = DataChangedEvent(data=data)
            evt.SetEventObject(self)
            wx.PostEvent(self.GetParent(), evt)

    # -----------------------------------------------------------------------
    # Public methods to navigate
    # -----------------------------------------------------------------------

    def show_page(self, page_name, fct="", args=None):
        """Show a page of the book.

        :param page_name: (str) one of 'page_annot_actions', 'page_...', ...
        :param fct: (str) a method of the page
        :param args: (any) args of the function

        """
        # Find the page number to switch on
        dest_w = self.FindWindow(page_name)
        if dest_w is None:
            dest_w = self.FindWindow("page_annot_actions")
        p = self.FindPage(dest_w)
        if p == -1:
            p = 0

        # Current page number
        c = self.FindPage(self.GetCurrentPage())  # current page position
        cur_w = self.GetPage(c)  # Returns the window at the given page position

        # Showing the current page is already done!
        if c == p:
            return

        # Assign the effect
        if c < p:
            self.SetEffects(showEffect=wx.SHOW_EFFECT_SLIDE_TO_TOP,
                            hideEffect=wx.SHOW_EFFECT_SLIDE_TO_TOP)
        elif c > p:
            self.SetEffects(showEffect=wx.SHOW_EFFECT_SLIDE_TO_BOTTOM,
                            hideEffect=wx.SHOW_EFFECT_SLIDE_TO_BOTTOM)

        # update param
        self.__param = cur_w.get_param()
        #self.__send_data(cur_w)
        dest_w.set_param(self.__param)

        # Change to the destination page
        self.ChangeSelection(p)
        dest_w.Refresh()

        # Call a method of the class
        if len(fct) > 0:
            try:
                if args is not None:
                    getattr(dest_w, fct)(args)
                else:
                    getattr(dest_w, fct)()
            except AttributeError as e:
                wx.LogError("Annotate show page. {:s}".format(str(e)))
