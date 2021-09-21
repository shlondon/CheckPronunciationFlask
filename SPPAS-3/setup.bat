GOTO EndHeader

:filename:     sppas.bat
:author:       Brigitte Bigi
:contact:      develop@sppas.org
:summary:      Launch the GUI setup of SPPAS for Windows.

.. _This file is part of SPPAS: http://www.sppas.org/
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

:EndHeader


@echo off
color 0F
SET PYTHONIOENCODING=UTF-8

REM Make sure we have admin right -- not required anymore
REM set "params=%*"
REM cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )

echo Search for python3.exe command
WHERE python3.exe
echo Status = %ERRORLEVEL%

if %ERRORLEVEL% EQU 0 (
    echo ... python3.exe found.
    color 1E
    echo Check if wxPython is installed or needs update...
    timeout /t 5
    start "" python3.exe .\sppas\bin\preinstall.py --wxpython
    echo ... done
) else (
    echo ... python3.exe not found
)
timeout /t 10

echo Search for python3w.exe command
WHERE pythonw3.exe >nul 2>nul

if %ERRORLEVEL% EQU 0 (
    echo ... pythonw3.exe found
    color 1E
    start "" pythonw3.exe .\sppas\bin\preinstallgui.py
    REM exit

) else (
    echo pythonw3.exe not found

    echo Search for python.exe command
    WHERE python.exe >nul 2>nul
    if %ERRORLEVEL% NEQ 9009 (

        echo Command python.exe was found.
        echo Launch checkpy script

        python.exe .\sppas\bin\checkpy.py
        if %ERRORLEVEL% EQU 0 (
            echo Launch preinstall script to install wx. Please wait...
            start "" python.exe .\sppas\bin\preinstall.py --wxpython
            echo Launch preinstall GUI script
            start "" python.exe .\sppas\bin\preinstallgui.py
            REM exit
        ) else (
            echo ... but this program requires Python version 3.
        )

    ) else (
        echo No Python command was not found.
        color 4E
        echo Python is not an internal command of your operating system
        echo or the environment variable wasn't fixed during its installation.
        echo Install or re-install it, preferably from the Windows Store.
    )
)

REM Close the windows with a delay to let some time to read messages
timeout /t 20
