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
import subprocess
import re
import pynag.Plugins
import shlex

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


class GitRepo(object):
    def __init__(self, directory):
        """
        Python Wrapper around Git command line.


        """

        self.directory = directory

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
            result.append( {'status':line[0], 'filename': line[1]} )
        return result
    def init(self):
        """ Initilizes a new git repo (i.e. run "git init") """
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


class PerfData(object):
    """ Data Structure for a nagios perfdata string with multiple perfdata metric

    Example string:
    >>> perf = PerfData("load1=10 load2=10 load3=20")
    >>> perf.metrics
    ['load1'=10.0;;;;, 'load2'=10.0;;;;, 'load3'=20.0;;;;]
    >>> for i in perf.metrics: print i.label, i.value
    load1 10.0
    load2 10.0
    load3 20.0
    """
    def __init__(self, perfdatastring=""):
        """ >>> perf = PerfData("load1=10 load2=10 load3=20") """
        self.metrics = []
        self.invalid_metrics = []
        # Hack: For some weird reason livestatus sometimes delivers perfdata in utf-32 encoding.
        perfdatastring = perfdatastring.replace('\x00','')
        try:
            perfdata = shlex.split(perfdatastring)
            for metric in perfdata:
                try:
                    self.add_perfdatametric( metric )
                except Exception:
                    self.invalid_metrics.append( metric )
        except ValueError:
            return

    def is_valid(self):
        """ Returns True if the every metric in the string is valid """
        for i in self.metrics:
            if not i.is_valid():
                return False
    def add_perfdatametric(self, perfdatastring="", label="",value="",warn="",crit="",min="",max="",uom=""):
        """ Add a new perfdatametric to existing list of metrics.

         Example:
         >>> s = PerfData()
         >>> s.add_perfdatametric("a=1")
         >>> s.add_perfdatametric(label="utilization",value="10",uom="%")
        """
        metric=PerfDataMetric(perfdatastring=perfdatastring, label=label,value=value,warn=warn,crit=crit,min=min,max=max,uom=uom)
        self.metrics.append(  metric )
    def get_perfdatametric(self, metric_name):
        """ Get one specific perfdatametric
        >>> s = PerfData("cpu=90% memory=50% disk_usage=20%")
        >>> my_metric = s.get_perfdatametric('cpu')
        >>> my_metric.label, my_metric.value
        ('cpu', 90.0)
        """
        for i in self.metrics:
            if i.label == metric_name:
                return i
    def __str__(self):
        metrics = map(lambda x: x.__str__(), self.metrics)
        return ' '.join(metrics)
    def __str__(self):
        metrics = map(lambda x: x.__repr__(), self.metrics)
        return ' '.join(metrics)

class PerfDataMetric(object):
    """ Data structure for one single Nagios Perfdata Metric """
    label = ""
    value = ""
    warn = ""
    crit = ""
    min = ""
    max = ""
    uom = ""
    def __repr__(self):
        return "'%s'=%s%s;%s;%s;%s;%s" % (
            self.label,
            self.value,
            self.uom,
            self.warn,
            self.crit,
            self.min,
            self.max,
            )
    def __str__(self):
        return """
            label: %s
            value: %s %s
            warning: %s
            critical: %s
            min: %s
            max: %s
            """ % (
            self.label,
            self.value,
            self.uom,
            self.warn,
            self.crit,
            self.min,
            self.max,
            )

    def __init__(self, perfdatastring="", label="",value="",warn="",crit="",min="",max="",uom=""):
        """
        >>> p = PerfData(perfdatastring="size=10M;20M;;;")
        >>> metric = p.get_perfdatametric('size')
        >>> print metric.label
        size
        >>> print metric.value
        10
        >>> print metric.uom
        M
        """
        self.label = label
        self.value = value
        self.warn = warn
        self.crit = crit
        self.min = min
        self.max = max
        self.uom = uom

        perfdatastring = str(perfdatastring)

        # Hack: For some weird reason livestatus sometimes delivers perfdata in utf-32 encoding.
        perfdatastring = perfdatastring.replace('\x00','')
        if len(perfdatastring) == 0:
            return

        # If label is single quoted, there might be any symbol in the label
        # including other single quotes and the = sign. Therefore, we take special precautions if it is so
        if perfdatastring.startswith("'"):
            tmp = perfdatastring.split("'")
            everything_but_label = tmp.pop()
            tmp.pop(0)
            label = "'".join(tmp)
        else:
            label, everything_but_label = perfdatastring.split('=', 1)
        self.label = label

        # Next split string into value;warning;critical;min;max
        tmp = everything_but_label.split(';')
        if len(tmp) > 0:
            val = tmp.pop(0).strip('=')
            self.value, self.uom = self.split_value_and_uom(val)
        if len(tmp) > 0:
            self.warn = tmp.pop(0)
        if len(tmp) > 0:
            self.crit = tmp.pop(0)
        if len(tmp) > 0:
            self.min = tmp.pop(0)
        if len(tmp) > 0:
            self.max = tmp.pop(0)
        self.value = float(self.value)
    def get_status(self):
        """ Return nagios-style exit code (int 0-3) by comparing

          self.value with self.warn and self.crit
        """
        status = pynag.Plugins.check_threshold(self.value, warning=self.warn, critical=self.crit)
        return status


    def is_valid(self):
        """ Returns True if all Performance data is valid. Otherwise False """
        try:
            self.value == '' or float(self.value)
        except ValueError:
            return False
        try:
            self.min == '' or float(self.min)
        except ValueError:
            return False
        try:
            self.max == '' or float(self.max)
        except ValueError:
            return False
        if self.label.find(' ') > -1 and not self.label.startswith("'") and not self.label.endswith("'"):
            return False


    def split_value_and_uom(self, value):
        """ get value="10M" and return (10,"M")
        >>> p = PerfDataMetric()
        >>> p.split_value_and_uom( "10" )
        ('10', '')
        >>> p.split_value_and_uom( "10c" )
        ('10', 'c')
        >>> p.split_value_and_uom( "10B" )
        ('10', 'B')
        >>> p.split_value_and_uom( "10MB" )
        ('10', 'MB')
        >>> p.split_value_and_uom( "10KB" )
        ('10', 'KB')
        >>> p.split_value_and_uom( "10TB" )
        ('10', 'TB')
        >>> p.split_value_and_uom( "10%" )
        ('10', '%')
        >>> p.split_value_and_uom( "10s" )
        ('10', 's')
        >>> p.split_value_and_uom( "10us" )
        ('10', 'us')
        >>> p.split_value_and_uom( "10ms" )
        ('10', 'ms')
        """
        tmp = re.findall(r"([-]*[\d.]*\d+)(.*)", value)
        if len(tmp) == 0:
            return '',''
        return tmp[0]
