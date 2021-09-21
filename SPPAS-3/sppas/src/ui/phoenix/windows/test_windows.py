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

    src.ui.phoenix.tests.test_windows.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import sys
import wx
import logging
sppas_dir = os.getenv("SPPAS")
sys.path.insert(0, sppas_dir)
from sppas.src.config import sppasAppConfig
from sppas.src.ui.phoenix.main_settings import WxAppSettings

# Tested files are the ones with a TestPanel class:
import sppas.src.ui.phoenix.windows.basedcwindow as basedcwindow
import sppas.src.ui.phoenix.windows.baselabelwindow as labelwindow
import sppas.src.ui.phoenix.windows.basewindow as basewindow
import sppas.src.ui.phoenix.windows.toolbar as toolbar
import sppas.src.ui.phoenix.windows.line as line
import sppas.src.ui.phoenix.windows.label as label
import sppas.src.ui.phoenix.windows.slider as slider
import sppas.src.ui.phoenix.windows.buttonbox as buttonbox
import sppas.src.ui.phoenix.windows.combobox as combobox
import sppas.src.ui.phoenix.windows.popup as popup
import sppas.src.ui.phoenix.windows.listctrl as listctrl
import sppas.src.ui.phoenix.windows.frame as frame

# ----------------------------------------------------------------------------
# Panel to test
# ----------------------------------------------------------------------------


class TestPanel(wx.Choicebook):
    def __init__(self, parent):
        wx.Choicebook.__init__(
            self,
            parent,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL | wx.WANTS_CHARS)
        self.AddPage(buttonbox.TestPanelRadioBox(self), "RadioBox & ToggleBox")

        self.AddPage(basedcwindow.TestPanel(self), "Base DC Window")
        self.AddPage(labelwindow.TestPanel(self), "Label Window")
        self.AddPage(label.TestPanel(self), "Header Window")
        self.AddPage(basewindow.TestPanel(self), "Base Focused Window")
        self.AddPage(line.TestPanel(self), "Lines")
        self.AddPage(slider.TestPanel(self), "Slider")
        self.AddPage(toolbar.TestPanel(self), "Toolbar")
        self.AddPage(listctrl.TestPanel(self), "ListCtrl")
        self.AddPage(combobox.TestPanelComboBox(self), "ComboBox")
        self.AddPage(popup.TestPanel(self), "Popup")
        self.AddPage(frame.TestPanel(self), "Frame")

        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(wx.EVT_KEY_DOWN, self._process_key_event)

    # -----------------------------------------------------------------------

    def _process_key_event(self, event):
        """Process a key event.

        :param event: (wx.Event)

        """
        key_code = event.GetKeyCode()

        # Keeps on going the event to the current page of the book.
        event.Skip()

    # -----------------------------------------------------------------------

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

# ----------------------------------------------------------------------------
# App to test
# ----------------------------------------------------------------------------


class TestApp(wx.App):

    def __init__(self):
        """Create a customized application."""
        # ensure the parent's __init__ is called with the args we want
        wx.App.__init__(self,
                        redirect=False,
                        filename=None,
                        useBestVisual=True,
                        clearSigInt=True)

        # create the frame
        frm = wx.Frame(None, title='Test frame', size=wx.Size(900, 600))
        frm.SetMinSize(wx.Size(640, 480))
        self.SetTopWindow(frm)

        # Fix language and translation
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        self.__cfg = sppasAppConfig()
        self.settings = WxAppSettings()
        self.setup_debug_logging()

        # create a panel in the frame
        sizer = wx.BoxSizer()
        sizer.Add(TestPanel(frm), 1, wx.EXPAND, 0)
        frm.SetSizer(sizer)

        # show result
        frm.Show()
        frm.Layout()

    @staticmethod
    def setup_debug_logging():
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logging.debug('Logging set to DEBUG level')

# ---------------------------------------------------------------------------


if __name__ == '__main__':
    app = TestApp()
    app.MainLoop()
