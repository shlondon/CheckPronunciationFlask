# -*- coding: UTF-8 -*-
"""
:filename: sppas.src.config.process.py
:authors: Florian Hocquet, Brigitte Bigi
:contact: develop@sppas.org
:summary: Execute a subprocess and get results.

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

import os
import shlex
import logging
import signal
import subprocess

# ------------------------------------------------------------------------


class Process(object):
    """A convenient class to execute a subprocess.

    A Process is a wrapper of subprocess.Popen command.

    Launch a command:
        >>> p = Process()
        >>> p.run_popen("ls -l")

    Return the stdout of the command:
        >>> p.out()

    Return the stderr of the command:
        >>> p.error()

    Stop a command:
        >>> p.stop()

    Return the state of the command:
        >>> p.is_running()

    """

    def __init__(self):
        """Create a new instance."""
        self.__process = None

    # ------------------------------------------------------------------------

    @staticmethod
    def test_command(command):
        """Return True if command exists.

        Test only the main command (i.e. the first string, without args).

        """
        logging.debug("Test of the command: {:s}".format(command))
        command_args = shlex.split(command)
        test_command = command_args[0]

        NULL = open(os.path.devnull, 'w')
        try:
            p = subprocess.Popen([test_command], shell=False, stdout=NULL, stderr=NULL)
        except OSError:
            NULL.close()
            return False

        # Get the process id & try to terminate it gracefully
        pid = p.pid
        p.terminate()

        # Check if the process has really terminated & force kill if not.
        try:
            os.kill(pid, signal.SIGINT)
            p.kill()
            # print("Forced kill")
        except OSError:
            # print("Terminated gracefully")
            pass
        NULL.close()
        return True

    # ------------------------------------------------------------------------

    def run_popen(self, command):
        """Execute the given command with subprocess.Popen.

        :param command: (str) The command to be executed

        """
        logging.info("Process command: {}".format(command))
        command = command.strip()
        command_args = shlex.split(command)
        pipe = subprocess.PIPE
        self.__process = subprocess.Popen(command_args, stdout=pipe, stderr=pipe)  #, text=True)
        self.__process.wait()

    # ------------------------------------------------------------------------

    def run(self, command, timeout=120):
        """Execute command with subprocess.run.

        :param command: (str) The command to execute
        :param timeout: (int) Will raise TimeoutExpired() after timeout seconds

        """
        logging.info("Process command: {}".format(command))
        command = command.strip()
        command_args = shlex.split(command)
        self.__process = subprocess.run(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=None,
            timeout=timeout,
            check=False,
            encoding=None,
            errors=None,
            # text=None,   # does not work with python 3.6
            env=None,
            universal_newlines=True)

    # ------------------------------------------------------------------------

    def out(self):
        """Return the standard output of the process.

        :return: (str) output message

        """
        if self.__process is None:
            return ""
        out = self.__process.stdout  #.read()
        out = str(out)
        return out

    # ------------------------------------------------------------------------

    def error(self):
        """Return the error output of the process.

        :return: (str) error message

        """
        if self.__process is None:
            return ""
        error = self.__process.stderr  #.read()
        error = str(error)
        return error

    # ------------------------------------------------------------------------

    def stop(self):
        """Terminate the process if it is running."""
        if self.is_running() is True:
            self.__process.terminate()

    # ------------------------------------------------------------------------

    def status(self):
        """Return the status of the command if the process is completed.

        :return: (int) -2 is no process

        """
        if self.__process is None:
            return -2
        return self.__process.returncode

    # ------------------------------------------------------------------------

    def is_running(self):
        """Return True if the process is still running.

        :return: (bool)

        """
        if self.__process is None:
            return False
        return self.__process.poll() is None
