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

"""
This module is experimental.

The idea is to create a mechanism that allows you to hook your own events into
an ObjectDefinition instance.

This enables you for example to log to file every time an object is rewritten.
"""


import time
from platform import node
from os.path import dirname
import subprocess
import shlex
from os import environ
from getpass import getuser

class BaseEventHandler:
    def __init__(self, debug=False):
        self._debug = debug
    def debug(self, object_definition, message):
        """Used for any particual debug notifications"""
        raise NotImplementedError()
    def write(self, object_definition, message):
        """Called whenever a modification has been written to file"""
        raise NotImplementedError()
    def pre_save(self, object_definition, message):
        """ Called at the beginning of save() """
    def save(self, object_definition, message):
        """Called when objectdefinition.save() has finished"""
        raise NotImplementedError()


class PrintToScreenHandler(BaseEventHandler):
    """Handler that prints everything to stdout"""
    def debug(self, object_definition, message):
        """Used for any particual debug notifications"""
        if self._debug:
            print "%s: %s" % ( time.asctime(), message )
    def write(self, object_definition, message):
        """Called whenever a modification has been written to file"""
        print "%s: file='%s' %s" % ( time.asctime(), object_definition['meta']['filename'], message )
    def save(self, object_definition, message):
        """Called when objectdefinition.save() has finished"""
        print "%s: %s" % ( time.asctime(), message )


class FileLogger(BaseEventHandler):
    """Handler that logs everything to file"""
    def __init__(self, logfile='/var/log/pynag.log', debug=False):
        BaseEventHandler.__init__(self)
        self.file = logfile
        self._debug = debug
    def _append_to_file(self, message):
        f = open(self.file, 'a')
        if not message.endswith('\n'): message += '\n'
        f.write( message  )
        f.close()
    def debug(self, object_definition, message):
        """Used for any particular debug notifications"""
        if self.debug:
            message = "%s: %s" % ( time.asctime(), message )
            self._append_to_file( message )
    def write(self, object_definition, message):
        """Called whenever a modification has been written to file"""
        message = "%s: file='%s' %s" %( time.asctime(), object_definition['meta']['filename'], message )
        self._append_to_file( message )
    def save(self, object_definition, message):
        """Called when objectdefinition.save() has finished"""
        message = "%s: %s" %( time.asctime(), message )
        self._append_to_file( message )


class GitEventHandler(BaseEventHandler):
    def __init__(self, gitdir, source, modified_by, auto_init=False, ignore_errors=False):
        """
        Commits to git repo rooted in nagios configuration directory

        It automatically raises an exception if the configuration directory
        is not a git repository.

        source = prepended to git commit messages
        modified_by = is the username in username@<hostname> for commit messages
        ignore_errors = if True, do not raise exceptions on git errors
        auto_init = If True, run git init if no git repository is found.
        """
        BaseEventHandler.__init__(self)
        import subprocess

        # Git base is the nagios config directory
        self.gitdir = gitdir

        # Who made the change
        self.modified_by = modified_by

        # Which program did the change
        self.source = source

        # Every string in self.messages indicated a line in the eventual commit message
        self.messages = []

        self.ignore_errors = ignore_errors
        if auto_init:
            try:
                self._run_command('git status --short')
            except EventHandlerError, e:
                if e.errorcode == 128:
                    self._git_init()
        #self._run_command('git status --short')

        self._update_author()
    def debug(self, object_definition, message):
        pass
    def _update_author(self):
        """ Updates environment variables GIT_AUTHOR_NAME and EMAIL

        Returns: None
        """
        environ['GIT_AUTHOR_NAME'] = self.modified_by
        environ['GIT_AUTHOR_EMAIL'] = "%s@%s" % (self.source, node())
    def _run_command(self, command):
        """ Run a specified command from the command line. Return stdout """
        import subprocess
        import os
        cwd = self.gitdir
        proc = subprocess.Popen(command, cwd=cwd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate('through stdin to stdout')
        returncode = proc.returncode
        if returncode > 0 and self.ignore_errors == False:
            errorstring = "Command '%s' returned exit status %s.\n stdout: %s \n stderr: %s\n Current user: %s"
            errorstring = errorstring % (command, returncode, stdout, stderr,getuser())
            raise EventHandlerError( errorstring, errorcode=returncode, errorstring=stderr )
        return stdout
    def is_commited(self):
        """ Returns True if all files in git repo are fully commited """
        return self.get_uncommited_files() == 0
    def get_uncommited_files(self):
        """ Returns a list of files that are have unstaged changes """
        output = self._run_command("git status --porcelain")
        result = []
        for line in output.split('\n'):
            line = line.split()
            if len(line) < 2:
                continue
            result.append( {'status':line[0], 'filename': " ".join(line[1:])} )
        return result
    def _git_init(self, directory=None):
        """ Initilizes a new git repo in directory. If directory is none, use self.gitdir """
        self._update_author()
        command = "git init"
        self._run_command("git init")
        self._run_command("git add .")
        self._run_command("git commit -a -m 'Initial Commit'")

    def _git_add(self, filename):
        """ Wrapper around git add command """
        self._update_author()
        directory = dirname(filename)
        command= "git add '%s'" % filename
        return self._run_command(command)
    def _git_commit(self, filename, message, filelist=[]):
        """ Wrapper around git commit command """
        self._update_author()
        # Lets strip out any single quotes from the message:
        message = message.replace("'",'"')
        if len(filelist) > 0:
            filename = "' '".join(filelist)
        command = "git commit '%s' -m '%s'" % (filename, message)
        return self._run_command(command=command)
    def pre_save(self, object_definition, message):
        """ Commits object_definition.get_filename() if it has any changes """
        filename = object_definition.get_filename()
        if self._is_dirty(filename):
            self._git_add(filename)
            self._git_commit(filename,
                message="External changes commited in %s '%s'" %
                        (object_definition.object_type, object_definition.get_shortname()))
    def save(self, object_definition, message):
        filename = object_definition.get_filename()
        if len(self.messages) > 0:
            message = [message, '\n'] + self.messages
            message = '\n'.join(message)
        self._git_add(filename)
        if self._is_dirty(filename):
            self._git_commit(filename, message)
        self.messages = []
    def _is_dirty(self,filename):
        """ Returns True if filename needs to be committed to git """
        command = "git status --porcelain '%s'" % filename
        output = self._run_command(command)
        # Return True if there is any output
        return len(output) > 0
    def write(self, object_definition, message):
        # When write is called ( something was written to file )
        # We will log it in a buffer, and commit when save() is called.
        self.messages.append( " * %s" % message )




class EventHandlerError(Exception):
    pass
    def __init__(self, message, errorcode=None, errorstring=None):
        self.message = message
        self.errorcode = errorcode
        self.errorstring = errorstring
    def __str__(self):
        return self.errorstring
