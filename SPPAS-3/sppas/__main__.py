#!/usr/bin/env python
"""
:filename: sppas.__main__.py
:author: Brigitte Bigi
:contact: develop@sppas.org
:summary: Main file to launch the Graphical User Interface of SPPAS

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

In Python, '__main__' is the name of the scope in which top-level code
executes. Within SPPAS, it allows to launch the Graphical User Interface.

To launch the GUI, this main file allows the followings 3 solutions:

>>> python3 -m sppas
>>> python3 sppas
>>> python3 sppas/__main__.py

In case of error, SPPAS creates a log file with the error message and it
displays it.

"""

# Import of python standard libraries
import sys
import os
import webbrowser
import time
import traceback
if sys.version_info < (3, 6):
    print("[ ERROR ] Python needs to be updated. SPPAS requires version 3.8+.")
    print("* * * * *  SPPAS exited with error: Invalid python  * * * * * ")
    time.sleep(10)
    sys.exit(1)
if sys.version_info < (3, 8):
    print("[ WARNING ] Python should to be updated. SPPAS requires version 3.8+.")

# package is not defined if the program is launched without -m option
if __package__ is None or len(__package__) == 0:
    sppas_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, sppas_dir)
    __package__ = "sppas"

try:
    from sppas.src.config import cfg
    from sppas.src.config import sppasLogFile
    from sppas.src.config import sppasEnableFeatureError
    from sppas.src.config import sppasPackageFeatureError
    from sppas.src.config import sppasPackageUpdateFeatureError
    from sppas.src.ui.phoenix import sppasApp
except Exception as e:
    # The API wasn't imported.
    # Something is wrong with the installation of python, wxpython or SPPAS.
    msg = traceback.format_exc()
    try:
        status = e.status
    except:
        status = 1
    print(msg)
    print("* * * * *  SPPAS exited with error number: {:04d}  * * * * * ".format(status))
    webbrowser.open(url="http://www.sppas.org/documentation_09_annexes.html#error-" + "{:04d}".format(status))
    time.sleep(10)
    sys.exit(1)

# The API was successfully imported
status = 1
msg = ""
try:
    # Create and run the wx application
    app = sppasApp()
    status = app.run()
except sppasEnableFeatureError as e:
    # wxpython feature is not enabled
    print(traceback.format_exc())
    status = e.status
    msg = str(e)
except sppasPackageFeatureError as e:
    # wxpython is enabled but wx can't be imported
    print(traceback.format_exc())
    status = e.status
    msg = str(e)
except sppasPackageUpdateFeatureError as e:
    # wxpython is enabled but the version is not the right one
    print(traceback.format_exc())
    status = e.status
    msg = str(e)
except Exception as e:
    # any other error...
    print(traceback.format_exc())
    msg = str(e)

if status != 0:
    # open the report to display its content
    report = sppasLogFile(pattern="run")
    with open(report.get_filename(), "w") as f:
        f.write(report.get_header())
        f.write(msg)
        f.write("\n")
        f.write("\n")
        f.write("SPPAS application exited with error status: {:d}.".format(status))
    webbrowser.open(url=report.get_filename())
else:
    # save current configuration and exit with the appropriate status
    cfg.save()

sys.exit(status)
