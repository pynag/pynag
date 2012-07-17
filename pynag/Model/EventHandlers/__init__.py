# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2010 Pall Sigurdsson
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

'''
This module is experimental.

The idea is to create a mechanism that allows you to hook your own events into 
an ObjectDefinition instance.

This enables you for example to log to file every time an object is rewritten.
'''


import time

class BaseEventHandler:
    def __init__(self, debug=False):
        self._debug = debug
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
        if self._debug:
            print "%s: %s" %( time.asctime(), message )
    def write(self, object_definition, message):
        "Called whenever a modification has been written to file"
        print "%s: file='%s' %s" %( time.asctime(), object_definition['meta']['filename'], message )
    def save(self, object_definition, message):
        "Called when objectdefinition.save() has finished"
        print "%s: %s" %( time.asctime(), message )


class FileLogger(BaseEventHandler):
    "Handler that logs everything to file"
    def __init__(self, logfile='/var/log/pynag.log', debug=False):
        self.file = logfile
        self._debug = debug
    def _append_to_file(self, message):
        f = open(self.file, 'a')
        if not message.endswith('\n'): message += '\n'
        f.write( message  )
        f.close()
    def debug(self, object_definition, message):
        "Used for any particular debug notifications"
        if self.debug:
            message = "%s: %s" % ( time.asctime(), message )
            self._append_to_file( message )
    def write(self, object_definition, message):
        "Called whenever a modification has been written to file"
        message = "%s: file='%s' %s" %( time.asctime(), object_definition['meta']['filename'], message )
        self._append_to_file( message )
    def save(self, object_definition, message):
        "Called when objectdefinition.save() has finished"
        message = "%s: %s" %( time.asctime(), message )
        self._append_to_file( message )
 
 
class GitEventHandler(BaseEventHandler):
    def __init__(self, gitdir, source, modified_by):
        """
        Commits to git repo rooted in nagios configuration directory
        
        It automatically raises an exception if the configuration directory
        is not a git repository.
        
        source = prepended to git commit messages
        modified_by = is the username in username@<hostname> for commit messages
        """
        import git
        from os import environ
        from platform import node

        # Git base is the nagios config directory
        self.gitdir = gitdir

        # Who made the change
        self.modified_by = modified_by

        # Which program did the change
        self.source = source

        # Init the git repository
        try:
            self.gitrepo = git.Repo(self.gitdir)
        except Exception, e:
            raise Exception("Unable to open git repo %s, do you need to git init?" % (str(e)))

        # Set the author information for the commit
        environ['GIT_AUTHOR_NAME'] = self.modified_by
        environ['GIT_AUTHOR_EMAIL'] = "%s@%s" % (self.modified_by, node())

    def debug(self, object_definition, message):
        pass

    def write(self, object_definition, message):
        self.gitrepo.index.add([object_definition._meta['filename']])
        self.gitrepo.index.commit("%s: %s %s modified by %s" % (self.source, object_definition.object_type.capitalize(), object_definition.get_shortname(), self.modified_by))

    def save(self, object_definition, message):
        pass


