# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2010 Drew Stinnet
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


""" Misc utility classes and helper functions for pynag

This module contains misc classes and conveninence functions
that are used throughout the pynag library.

"""


class PynagError(Exception):
    """ The default pynag exception.

    Exceptions raised within the pynag library should aim
    to inherit this one.

    """



def runCommand(command, raise_error_on_fail=False):
    """ Run command from the shell prompt. Wrapper around subprocess.

     Arguments:
         command: string containing the command line to run
         raise_error_on_fail: Raise PynagError if returncode >0
     Returns:
         stdout/stderr of the command run
     Raises:
         PynagError if returncode > 0
     """
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
    stdout, stderr = proc.communicate('through stdin to stdout')
    result = proc.returncode,stdout,stderr
    if proc.returncode > 0 and raise_error_on_fail==True:
        error_string = "* Could not run command (return code= %s)\n" % proc.returncode
        error_string += "* Error was:\n%s\n" % (stderr.strip())
        error_string += "* Command was:\n%s\n" % command
        error_string += "* Output was:\n%s\n" % (stdout.strip())
        if proc.returncode == 127: # File not found, lets print path
            path=getenv("PATH")
            error_string += "Check if y/our path is correct: %s" % path
        raise PynagError( error_string )
    else:
        return result