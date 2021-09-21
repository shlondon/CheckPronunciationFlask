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

    src.ui.phoenix.page_annotate.annotevent.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import wx.lib.newevent

EVT_ANNOT_PAGE_CHANGE = wx.PyEventBinder(wx.NewEventType(), 1)


class sppasAnnotBookPageChangeEvent(wx.PyCommandEvent):
    """Class for an event sent when an action requires to change the page.

    The binder of this event is EVT_PAGE_CHANGE.

    """

    def __init__(self, event_id):
        """Default class constructor.

        :param event_id: the event identifier.

        """
        super(sppasAnnotBookPageChangeEvent, self).__init__(EVT_ANNOT_PAGE_CHANGE.typeId, event_id)
        self.__to_page = ""
        self.__fct = ""
        self.__args = None

    # -----------------------------------------------------------------------

    def SetToPage(self, value):
        """Set the name of the destination page of the book.

        :param value: (str) Name of a page.

        """
        self.__to_page = str(value)

    # -----------------------------------------------------------------------

    def GetToPage(self):
        """Return the name of the destination page of the book.

        :returns: (str)

        """
        return self.__to_page

    # -----------------------------------------------------------------------

    def SetFctName(self, name):
        """Name of a function the destination page has to launch.

        :param name: (str) Name of a function of the destination page.

        """
        self.__fct = str(name)

    # -----------------------------------------------------------------------

    def GetFctName(self):
        """Return the name of the function the destination page will run.

        :returns: (str) Empty string if no function

        """
        return self.__fct

    # -----------------------------------------------------------------------

    def SetFctArgs(self, args):
        """Arguments for the function.

        :param args: ()

        """
        self.__args = args

    # -----------------------------------------------------------------------

    def GetFctArgs(self):
        """Return the arguments for the function the destination page will run.

        :returns: () None if no arguments

        """
        return self.__args
