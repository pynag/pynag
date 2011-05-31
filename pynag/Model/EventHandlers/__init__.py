# -*- coding: utf-8 -*-
#
# Copyright 2010, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# About this module
# This module contains some pre-defined EventHandlers for the pynag.Model module.
# For example the FileLogger EventHandler gives log capabilities to pynag.Model

'''
This module is experimental.

The idea is to create a mechanism that allows you to hook your own events into 
an ObjectDefinition instance.

This enables you for example to log to file every time an object is rewritten.
'''


import time

class BaseEventHandler:
    def debug(self, object_definition, message):
        "Used for any particual debug notifications"
        raise NotImplementedError()
    def write(self, object_definition, message):
        "Called whenever a modification has been written to file"
        raise NotImplementedError()
    def save(self, object_definition, message):
        "Called when objectdefinition.save() has finished"
        raise NotImplementedError()


class PrintToScreenHandler(BaseEventHandler):
    "Handler that prints everything to stdout"
    def debug(self, object_definition, message):
        "Used for any particual debug notifications"
        print "%s: %s" %( time.asctime(), message )
    def write(self, object_definition, message):
        "Called whenever a modification has been written to file"
        print "%s: %s" %( time.asctime(), message )
    def save(self, object_definition, message):
        "Called when objectdefinition.save() has finished"
        print "%s: %s" %( time.asctime(), message )


class FileLogger(BaseEventHandler):
    "Handler that logs everything to file"
    def __init__(self, logfile='/var/log/pynag.log'):
        self.file = logfile
    def _append_to_file(self, message):
        f = open(self.file, 'a')
        f.write( message )
        f.close()
    def debug(self, object_definition, message):
        "Used for any particual debug notifications"
        self._append_to_file( "%s: %s" %( time.asctime(), message ))
    def write(self, object_definition, message):
        "Called whenever a modification has been written to file"
        self._append_to_file( "%s: %s" %( time.asctime(), message ))
    def save(self, object_definition, message):
        "Called when objectdefinition.save() has finished"
        self._append_to_file( "%s: %s" %( time.asctime(), message ))