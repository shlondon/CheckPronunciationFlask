GOTO EndHeader

:filename:     sppas.bat
:author:       Brigitte Bigi
:contact:      develop@sppas.org
:summary:      Launch the GUI of SPPAS for Windows.

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

SET PYTHONIOENCODING=UTF-8

WHERE pythonw3.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (

    start "" pythonw3.exe sppas
    if %ERRORLEVEL% EQU 0 (
        exit
    )

) else (

    WHERE python3.exe >nul 2>nul
    if %ERRORLEVEL% NEQ 9009 (
        color 1E
        start "" python3.exe sppas
        if %ERRORLEVEL% EQU 0 (
            exit
        )

    ) else (

        color 04

        if exist C:\Python27\pythonw.exe (
            echo [ WARNING ] Python needs to be updated. This is the last version of SPPAS that is supporting this old version. The next version of SPPAS will require version 3.8+.
            start "" C:\Python27\pythonw.exe .\sppas\bin\sppasgui.py
            exit
        ) else (
            if exist C:\Python27\python.exe (
                echo [ WARNING ] Python needs to be updated. This is the last version of SPPAS that is supporting this old version. The next version of SPPAS will require version 3.8+.
                start "" C:\Python27\python.exe .\sppas\bin\sppasgui.py
                exit
            ) else (

                REM Perhaps python3 was installed with name "python"
                WHERE python.exe >nul 2>nul
                if %ERRORLEVEL% NEQ 9009 (
                    python.exe .\sppas\bin\checkpy.py
                    if %ERRORLEVEL% NEQ 9009 (
                        start "" python.exe -m sppas
                        exit
                    ) else (
                        echo [ WARNING ] Python needs to be updated. This is the last version of SPPAS that is supporting this old version. The next version of SPPAS will require version 3.8+.
                        start "" python.exe .\sppas\bin\sppasgui.py
                        exit
                    )

                ) else (
                        color 4E
                        echo Python is not an internal command of your operating system.
                        echo Install it first with the Windows Store or from http://www.python.org.
                )
            )
        )
    )
)

REM Close the windows which was opened
timeout /t 20


