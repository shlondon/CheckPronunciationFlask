#!/bin/bash
# -*- coding: UTF-8 -*-
# ---------------------------------------------------------------------------
# Filename: sppas.command
# Author:   Brigitte Bigi
# Contact:  develop@sppas.org
# Summary:  Launch the GUI of SPPAS for MacOS/Linux.
# ---------------------------------------------------------------------------
#            ___   __    __    __    ___
#           /     |  \  |  \  |  \  /              the automatic
#           \__   |__/  |__/  |___| \__             annotation and
#              \  |     |     |   |    \             analysis
#           ___/  |     |     |   | ___/              of speech
#
#                           http://www.sppas.org/
#
# ---------------------------------------------------------------------------
#                   Copyright (C) 2011-2021  Brigitte Bigi
#            Laboratoire Parole et Langage, Aix-en-Provence, France
# ---------------------------------------------------------------------------
#                   This banner notice must not be removed
# ---------------------------------------------------------------------------
# Use of this software is governed by the GNU Public License, version 3.
#
# SPPAS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPPAS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SPPAS. If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------


# ===========================================================================
# Fix global variables
# ===========================================================================

# Fix the locale with a generic value!
LANG='C'

# Program infos
PROGRAM_DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)


# ===========================================================================
# MAIN
# ===========================================================================
export PYTHONIOENCODING=UTF-8

PYTHON=""
v="0"

# Search for python, version 3
# ------------------------------------------------------
echo -n "Search for 'python3' command for Python: "
for cmd in `which -a python3`;
do
    v=$($cmd -c "import sys; print(sys.version_info[0])");
    if [[ "$v" == "3" ]]; then
        PYTHON=$cmd;
        break;
    fi;
done

if [ -z "$PYTHON" ]; then
    echo "not found."
    echo -n "Search for 'python' command for Python 3: "
    for cmd in `which -a python`;
    do
        v=$($cmd -c "import sys; print(sys.version_info[0])");
        if [[ "$v" == "3" ]]; then
            PYTHON=$cmd;
            break;
        fi;
    done
else
    echo "OK";
fi

# Search for python, version 2
# ------------------------------------------------------
if [ -z "$PYTHON" ]; then
    echo "not found.";
    echo -n "Search for 'python' command for Python 2: ";
    for cmd in `which -a python`;
    do
        v=$($cmd -c "import sys; print(sys.version_info[0])");
        if [[ "$v" == "2" ]]; then
            PYTHON=$cmd;
            echo "[ WARNING ] DEPRECATION: Python 2.7 reached the end of its life.";
            echo "This is the last version of SPPAS that is supporting this old python.";
            echo "The next version of SPPAS will require python version 3.8+.";
            echo "Please upgrade your Python to 3.8+ as Python 2.7 is no longer maintained.";
            break;
        fi;
    done
fi

echo;

if [ -z "$PYTHON" ]; then
    echo "not found.";
    echo "Python is not an internal command of your operating system.";
    echo "Install it first http://www.python.org. Then try again with SPPAS.";
    exit -1;
fi

# Get the name of the system
unamestr=`uname | cut -f1 -d'_'`;

echo "SPPAS will start with: ";
echo "  - Command: '$PYTHON' (version $v)";
echo "  - System:  $unamestr";
echo "  - Display:  $DISPLAY";
echo "  - Location: $PROGRAM_DIR";

if [ "$unamestr" == "CYGWIN" ]; then
    if [ -z $DISPLAY ]; then
       echo "[ ERROR ] Unable to access the X Display.";
       echo "Did you enabled XWin server?";
       exit -1;
    fi
fi

echo "Run the Graphical User Interface...";

if [ "$v" == "2" ]; then
    $PYTHON $PROGRAM_DIR/sppas/bin/sppasgui.py
else
    cd $PROGRAM_DIR
    $PYTHON sppas
fi

