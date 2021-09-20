#!/bin/bash
# -*- coding: UTF-8 -*-
# ---------------------------------------------------------------------------
# Filename: setup.command
# Author:   Brigitte Bigi
# Contact:  develop@sppas.org
# Summary:  Launch the GUI setup of SPPAS for MacOS/Linux.
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

# Exit status:
STATUS_SUCCESS=0
STATUS_NOPYTHON=1
STATUS_NOWX=2
STATUS_FAILED=3

# Fix the locale with a generic value!
LANG='C'

# Program info
PROGRAM_DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)

# Python info we'll try to find
PYTHON=""
v="0"

# Colors
BLACK='\e[0;30m'
WHITE='\e[1;37m'
LIGHT_GRAY='\e[0;37m'
DARK_GRAY='\e[1;30m'
BLUE='\e[0;34m'
DARK_BLUE='\e[1;34m'
GREEN='\e[0;32m'
LIGHT_GREEN='\e[1;32m'
CYAN='\e[0;36m'
LIGHT_CYAN='\e[1;36m'
RED='\e[0;31m'
LIGHT_RED='\e[1;31m'
PURPLE='\e[0;35m'
LIGHT_PURPLE='\e[1;35m'
BROWN='\e[0;33m'
YELLOW='\e[1;33m'
NC='\e[0m' # No Color


# ===========================================================================
# FUNCTIONS
# ===========================================================================

# Print an error message with a GUI or on stdout if no GUI found
# Parameters:
#   $1: message to print
function fct_error_message()
{
  TITLE_MSG="Cannot start SPPAS"
  if [ -n "$(command -v zenity)" ]; then
      zenity --error --title="$TITLE_MSG" --text="$1" --no-wrap
  elif [ -n "$(command -v kdialog)" ]; then
      kdialog --error "$1" --title "$TITLE_MSG"
  elif [ -n "$(command -v notify-send)" ]; then
      notify-send "ERROR: $TITLE_MSG" "$1"
  elif [ -n "$(command -v xmessage)" ]; then
      xmessage -center "ERROR: $TITLE_MSG: $1"
  else
      printf "ERROR: %s\n%s\n" "$TITLE_MSG" "$1"
  fi
}


# ===========================================================================
# MAIN
# ===========================================================================

export PYTHONIOENCODING=UTF-8

echo -n "Search for 'pythonw3' command for Python: "
for cmd in `which -a pythonw3`;
do
    v=$($cmd -c "import sys; print(sys.version_info[0])");
    if [[ "$v" == "3" ]]; then
        PYTHON=$cmd;
        break;
    fi;
done

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

echo;

if [ -z "$PYTHON" ]; then
    echo "not found.";
    fct_error_message "Python version 3 is not an internal command of your operating system. Install it first http://www.python.org.";
    exit $STATUS_NOPYTHON;
fi


# PYTHON 3 IS OK
# ===========================================================================

# Get the name of the system
unamestr=`uname | cut -f1 -d'_'`;

echo "This setup starts with: ";
echo "  - Command: '$PYTHON' (version $v)";
echo "  - System:  $unamestr";
echo "  - Display:  $DISPLAY";
echo "  - Location: $PROGRAM_DIR";

if [ -e .app~ ];  then rm .app~;  fi

$PYTHON $PROGRAM_DIR/sppas/bin/checkwx.py
if [ $? -ne 0 ] ; then
    echo "Run the installer program to install wxpython...";
    sudo $PYTHON $PROGRAM_DIR/sppas/bin/preinstall.py --wxpython
fi

$PYTHON $PROGRAM_DIR/sppas/bin/checkwx.py
if [ $? -ne 0 ] ; then

      fct_error_message "This setup failed to install automatically wxpython. See http://www.sppas.org/installation.html to do it manually."
      exit $STATUS_NOWX

fi


# WX library IS OK
# ===========================================================================

# Continue with the GUI for other requirements.
$PYTHON $PROGRAM_DIR/sppas/bin/preinstallgui.py
if [ $? -ne 0 ] ; then
    fct_error_message "This setup failed to install automatically the required packages. See http://www.sppas.org/installation.html to do it manually."
    exit $STATUS_FAILED
fi

exit $STATUS_SUCCESS
