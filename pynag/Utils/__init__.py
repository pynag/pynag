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
import shlex
from os import getenv, environ, listdir, path
from platform import node
from getpass import getuser
import datetime
import pynag.Plugins


class PynagError(Exception):
    """ The default pynag exception.

    Exceptions raised within the pynag library should aim
    to inherit this one.

    """
    def __init__(self, message, errorcode=None, errorstring=None, *args, **kwargs):
        self.errorcode = errorcode
        self.message = message
        self.errorstring = errorstring
        super(self.__class__, self).__init__(message, *args,**kwargs)


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
    result = proc.returncode, stdout, stderr
    if proc.returncode > 0 and raise_error_on_fail==True:
        error_string = "* Could not run command (return code= %s)\n" % proc.returncode
        error_string += "* Error was:\n%s\n" % (stderr.strip())
        error_string += "* Command was:\n%s\n" % command
        error_string += "* Output was:\n%s\n" % (stdout.strip())
        if proc.returncode == 127: # File not found, lets print path
            path = getenv("PATH")
            error_string += "Check if y/our path is correct: %s" % path
        raise PynagError( error_string )
    else:
        return result


class GitRepo(object):
    def __init__(self, directory,auto_init=True,author_name="Pynag User", author_email=None):
        """
        Python Wrapper around Git command line.

        Arguments:
          Directory   -- Which directory does the git repo reside in (i.e. '/etc/nagios')
          auto_init   -- If True and directory does not contain a git repo, create it automatically
          author_name -- Full name of the author making changes
          author_email -- Email used for commit messages, if None, then use username@hostname

        """

        self.directory = directory

        # Who made the change
        if author_name is None:
            author_name = "Pynag User"
        if author_email is None:
            author_email = "<%s@%s>" % (getuser(), node())
        self.author_name = author_name
        self.author_email = author_email

        # Which program did the change
        #self.source = source

        # Every string in self.messages indicated a line in the eventual commit message
        self.messages = []

        self.ignore_errors = False
        self._update_author()
        if auto_init:
            try:
                self._run_command('git status --short')
            except PynagError, e:
                if e.errorcode == 128:
                    self.init()
            #self._run_command('git status --short')

        self._is_dirty = self.is_dirty # Backwards compatibility

    def _update_author(self):
        """ Updates environment variables GIT_AUTHOR_NAME and EMAIL

        Returns: None
        """
        environ['GIT_AUTHOR_NAME'] = self.author_name
        environ['GIT_AUTHOR_EMAIL'] = self.author_email.strip('<').strip('>')
    def _run_command(self, command):
        """ Run a specified command from the command line. Return stdout """
        import subprocess
        import os
        cwd = self.directory
        proc = subprocess.Popen(command, cwd=cwd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate('through stdin to stdout')
        returncode = proc.returncode
        if returncode > 0 and self.ignore_errors == False:
            errorstring = "Command '%s' returned exit status %s.\n stdout: %s \n stderr: %s\n Current user: %s"
            errorstring = errorstring % (command, returncode, stdout, stderr,getuser())
            raise PynagError( errorstring, errorcode=returncode, errorstring=stderr )
        return stdout
    def is_up_to_date(self):
        """ Returns True if all files in git repo are fully commited """
        return len(self.get_uncommited_files()) == 0
    def get_valid_commits(self):
        """ Returns a list of all commit ids from git log
        """
        return map(lambda x: x.get('hash'), self.log())

    def get_uncommited_files(self):
        """ Returns a list of files that are have unstaged changes """
        output = self._run_command("git status --porcelain")
        result = []
        for line in output.split('\n'):
            line = line.split(None, 1)
            if len(line) < 2:
                continue
            status, filename = line[0], line[1]
            # If file has been renamed, git status shows output in the form of:
            # R nrpe.cfg -> nrpe.cfg~
            # We want only the last part of the filename
            if status == 'R':
                filename = filename.split('->')[1].strip()
            # If there are special characters in the name, git will double-quote the output
            # We will remove those quotes, but we cannot use strip because it will damage:
            # files like this: "\"filename with actual doublequotes\""
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]

            result.append({'status': status, 'filename': filename})
        return result

    def log(self, **kwargs):
        """ Returns a log of previous commits. Log is is a list of dict objects.

        Any arguments provided will be passed directly to pynag.Utils.grep() to filter the results.

        Examples:
          self.log(author_name='nagiosadmin')
          self.log(comment__contains='localhost')
        """
        raw_log =self._run_command("git log --pretty='%H\t%an\t%ae\t%at\t%s'")
        result = []
        for line in raw_log.splitlines():
            hash,author, authoremail, authortime, comment = line.split("\t", 4)
            result.append( {
                "hash": hash,
                "author_name": author,
                "author_email": authoremail,
                "author_time": datetime.datetime.fromtimestamp(float(authortime)),
                "timestamp": float(authortime),
                "comment": comment,
                })
        return grep(result, **kwargs)
    def diff(self, commit_id_or_filename=None):
        """ Returns diff (as outputted by "git diff") for filename or commit id.

        If commit_id_or_filename is not specified. show diff against all uncommited files.
        """
        if commit_id_or_filename in ('', None):
            command = "git diff"
        elif path.exists(commit_id_or_filename):
            commit_id_or_filename = commit_id_or_filename.replace("'",r"\'")
            command = "git diff '%s'" % commit_id_or_filename
        elif commit_id_or_filename in self.get_valid_commits():
            commit_id_or_filename = commit_id_or_filename.replace("'",r"\'")
            command = "git diff '%s'" % commit_id_or_filename
        else:
            raise  PynagError("%s is not a valid commit id or filename" % commit_id_or_filename)
        # Clean single quotes from parameters:
        return self._run_command(command)
    def show(self, commit_id,):
        """ Returns output from "git show" for a specified commit_id
        """
        if commit_id not in self.get_valid_commits():
            raise  PynagError("%s is not a valid commit id" % commit_id)
        command = "git show %s" % commit_id
        return self._run_command(command)

    def init(self):
        """ Initilizes a new git repo (i.e. run "git init") """
        self._update_author()
        command = "git init"
        self._run_command("git init")
        # Only do initial commit if there are files in the directory
        if not listdir(self.directory) == ['.git']:
            self.commit(message='Initial Commit')
    def _git_add(self, filename):
        """ Deprecated, use self.add() instead. """
        return self.add(filename)
    def _git_commit(self, filename, message, filelist=None):
        """ Deprecated. Use self.commit() instead."""
        if filename is None:
            filelist = []
        if not filename is None:
            filelist.append(filename)
        return self.commit(message=message, filelist=filelist )
    def pre_save(self, object_definition, message):
        """ Commits object_definition.get_filename() if it has any changes """
        filename = object_definition.get_filename()
        if self.is_dirty(filename):
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
        if self.is_dirty(filename):
            self._git_commit(filename, message)
        self.messages = []
    def is_dirty(self,filename):
        """ Returns True if filename needs to be committed to git """
        command = "git status --porcelain '%s'" % filename
        output = self._run_command(command)
        # Return True if there is any output
        return len(output) > 0
    def write(self, object_definition, message):
        # When write is called ( something was written to file )
        # We will log it in a buffer, and commit when save() is called.
        self.messages.append( " * %s" % message )
    def revert(self, commit):
        """ Revert some existing commits works like "git revert" """
        commit = commit.replace(r"'", r"\'")
        command = "git revert --no-edit -- '%s'" % commit
        return self._run_command(command)
    def commit(self, message='commited by pynag',filelist=None, author=None):
        """ Commit files with "git commit"

        Arguments:
          message      -- Message used for the git commit
          filelist     -- List of filenames to commit (if None, then commit all files in the repo)
          author       -- Author to use for git commit. If any is specified, overwrite self.author_name and self.author_email
        Returns:
          Returns stdout from the "git commit" shell command.
        """

        # Lets escape all single quotes from the message
        message = message.replace("'", r"\'")

        if author is None:
            author = "%s <%s>" % (self.author_name, self.author_email)

        # Escape all single quotes in author:
        author = author.replace("'", r"\'")

        if filelist is None:
            # If no files provided, commit everything
            self.add('.')
            command = "git commit -a -m '%s' --author='%s'" % (message, author)
            return self._run_command(command=command)
        elif isinstance(filelist, str):
            # in case filelist was provided as a string, consider to be only one file
            filelist = [filelist]

        # Remove from commit list files that have not changed:
        filelist = filter(lambda x: self.is_dirty(x), filelist)

        # Run "git add" on every file. Just in case they are untracked
        for i in filelist:
            self.add(i)

        # Change ['file1','file2'] into the string """ 'file1' 'file2' """
        filestring = ''

        # Escape all single quotes in filenames
        filelist = map(lambda x: x.replace("'", r"\'"), filelist )

        # Wrap filename inside single quotes:
        filelist = map(lambda x: "'%s'" % x, filelist )

        # If filelist is empty, we have nothing to commit and we will return as opposed to throwing error
        if not filelist:
            return
        # Create a space seperated string with the filenames
        filestring = ' '.join(filelist)
        command = "git commit -m '%s' --author='%s' -- %s" % (message, author,filestring)
        return self._run_command(command=command)

    def add(self, filename):
        """ Run git add on filename

            Arguments:
                filename -- name of one file to add,
            Returns:
                The stdout from "git add" shell command.
        """

        # Escape all single quotes in filename:
        filename = filename.replace("'", r"\'")

        command = "git add -- '%s'" % filename
        return_code, stdout, stderr = runCommand(command)
        return stdout


class PerfData(object):
    """ Data Structure for a nagios perfdata string with multiple perfdata metric

    Example string:
    >>> perf = PerfData("load1=10 load2=10 load3=20 'label with spaces'=5")
    >>> perf.metrics
    ['load1'=10;;;;, 'load2'=10;;;;, 'load3'=20;;;;, 'label with spaces'=5;;;;]
    >>> for i in perf.metrics: print i.label, i.value
    load1 10
    load2 10
    load3 20
    label with spaces 5
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
        """ Returns True if the every metric in the string is valid

        Example usage:
        >>> PerfData("load1=10 load2=10 load3=20").is_valid()
        True
        >>> PerfData("10b").is_valid()
        False
        >>> PerfData("load1=").is_valid()
        False
        >>> PerfData("load1=10 10").is_valid()
        False
        """
        for i in self.metrics:
            if not i.is_valid():
                return False

        # If we get here, all tests passed
        return True
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
        ('cpu', '90')
        """
        for i in self.metrics:
            if i.label == metric_name:
                return i
    def __str__(self):
        metrics = map(lambda x: x.__str__(), self.metrics)
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
        return self.__repr__()

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
        >>> p = PerfDataMetric(perfdatastring="'with spaces'=10")
        >>> print p.label
        with spaces
        >>> print p.value
        10
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
            # Split into label=perfdata
            tmp = perfdatastring.split('=', 1)
            # If no = sign, then we just take in a label
            if tmp:
                label = tmp.pop(0)
            if tmp:
                everything_but_label = tmp.pop()
            else:
                everything_but_label = ''

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
    def get_status(self):
        """ Return nagios-style exit code (int 0-3) by comparing

          self.value with self.warn and self.crit

          >>> PerfDataMetric("label1=10;20;30").get_status()
          0
          >>> PerfDataMetric("label2=25;20;30").get_status()
          1
          >>> PerfDataMetric("label3=35;20;30").get_status()
          2

          # Invalid metrics always return unknown
          >>> PerfDataMetric("label3=35;invalid_metric").get_status()
          3
        """
        try:
            status = pynag.Plugins.check_threshold(self.value, warning=self.warn, critical=self.crit)
        except pynag.Utils.PynagError:
            status = 3
        return status


    def is_valid(self):
        """ Returns True if all Performance data is valid. Otherwise False

        Example Usage:
        >>> PerfDataMetric("load1=2").is_valid()
        True
        >>> PerfDataMetric("load1").is_valid()
        False
        >>> PerfDataMetric('').is_valid()
        False
        >>> PerfDataMetric('invalid_value=invalid').is_valid()
        False
        >>> PerfDataMetric('invalid_min=0;0;0;min;0').is_valid()
        False
        >>> PerfDataMetric('invalid_min=0;0;0;0;max').is_valid()
        False
        >>> PerfDataMetric('label with spaces=0').is_valid()
        False
        >>> PerfDataMetric("'label with spaces=0'").is_valid()
        False
        """
        if self.label in (None, ''):
            return False

        if self.value in (None,''):
            return False

        try:
            float(self.value)
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

        # If we get here, we passed all tests
        return True


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


def grep(objects, **kwargs):
    """  Returns all the elements from array that match the keywords in **kwargs

    TODO: Refactor pynag.Model.ObjectDefinition.objects.filter() and reuse it here.
    Arguments:
        array -- a list of dict that is to be searched
        kwargs -- Any search argument provided will be checked against every dict
    Examples:
    array = [
    {'host_name': 'examplehost', 'state':0},
    {'host_name': 'example2', 'state':1},
    ]
    grep_dict(array, state=0)
    # should return [{'host_name': 'examplehost', 'state':0},]

    """
    # Input comes to us as a key/value dict.
    # We will flatten this out into a tuble, because if value
    # is a list, it means the calling function is doing multible search on
    # the same key
    search = []
    for k,v in kwargs.items():
        if type(v) == type([]):
            for i in v:
                search.append((k,i))
        else:
            search.append((k,v))
    matching_objects = objects
    for k,v in search:
        #v = str(v)
        if k.endswith('__contains'):
            k = k[:-len('__contains')]
            expression = lambda x: str(v) in str(x.get(k))
        elif k.endswith('__notcontains'):
            k = k[:-len('__notcontains')]
            expression = lambda x: not str(v) in str(x.get(k))
        elif k.endswith('__startswith'):
            k = k[:-len('__startswith')]
            expression = lambda x: str(x.get(k)).startswith(str(v))
        elif k.endswith('__endswith'):
            k = k[:-len('__endswith')]
            expression = lambda x: str(x.get(k)).endswith(str(v))
        elif k.endswith('__exists'):
            k = k[:-len('__exists')]
            expression = lambda x: str(x.has_key(k)) == str(v)
        elif k.endswith('__isnot'):
            k = k[:-len('__isnot')]
            expression = lambda x: str(v) != str(x.get(k))
        elif k.endswith('__regex'):
            k = k[:-len('__regex')]
            regex = re.compile(str(v))
            expression = lambda x: regex.search( str(x.get(k)) )
        elif k.endswith('__in'):
            k  = k = k[:-len('__in')]
            expression = lambda x: str(x.get(k)) in v
        elif k.endswith('__notin'):
            k  = k = k[:-len('__notin')]
            expression = lambda x: str(x.get(k)) in v
        elif k.endswith('__has_field'):
            k = k[:-len('__has_field')]
            expression = lambda x: str(v) in AttributeList(x.get(k)).fields
        elif k == 'register' and str(v) == '1':
            # in case of register attribute None is the same as "1"
            expression = lambda x: x.get(k) in (v, None)
        elif k in ('search','q'):
            expression = lambda x: str(v) in str(x)
        else:
            # If all else fails, assume they are asking for exact match
            expression = lambda x: str(x.get(k)) == str(v) or ( isinstance(x.get(k), list) and isinstance(v,str) and v in x.get(k) )
        matching_objects = filter(expression, matching_objects)
    return matching_objects

def grep_to_livestatus(*args,**kwargs):
    """ Converts from pynag style grep syntax to livestatus filter syntax.

    Example:
        >>> grep_to_livestatus(host_name='test')
        ['Filter: host_name = test']

        >>> grep_to_livestatus(service_description__contains='serv')
        ['Filter: service_description ~ serv']
    """
    result = list(args) # Args go unchanged back into results
    for k,v in kwargs.items():
        if isinstance(v,list) and len(v) > 0:
            v = v[0]
        if k.endswith('__contains'):
            k = k[:-len('__contains')]
            my_string = "Filter: %s ~ %s" % (k,v)
        elif k.endswith('__has_field'):
            k = k[:-len('__has_field')]
            my_string = "Filter: %s >= %s" % (k,v)
        elif k.endswith('__isnot'):
            k = k[:-len('__isnot')]
            my_string = "Filter: %s != %s" % (k,v)
        else:
            my_string = "Filter: %s = %s" % (k,v)
        result.append(my_string)
    return result

class AttributeList(object):
    """ Parse a list of nagios attributes (e. contact_groups) into a parsable format

    This makes it handy to mangle with nagios attribute values that are in a comma seperated format.

    Typical comma-seperated format in nagios configuration files looks something like this:
        contact_groups     +group1,group2,group3

    Example:
        >>> i = AttributeList('+group1,group2,group3')
        >>> print "Operator is:", i.operator
        Operator is: +
        >>> print i.fields
        ['group1', 'group2', 'group3']

        if your data is already in a list format you can use it directly:
        >>> i = AttributeList(['group1', 'group2', 'group3'])
        >>> print i.fields
        ['group1', 'group2', 'group3']

        white spaces will be stripped from all fields
        >>> i = AttributeList('+group1, group2')
        >>> print i
        +group1,group2

    """

    def __init__(self, value=None):
        self.operator = ''
        self.fields = []

        # this is easy to do if attribue_name is unset
        if not value or value == '':
            return

        # value in this case should usually be a comma seperated string, but sometimes
        # (like when working with livestatus) we have the luxury of getting lists
        if isinstance(value, list):
            # Remove empty fields
            self.fields = filter(lambda x: len(x) > 0, value)
            return

        possible_operators = '+-!'
        if value[0] in possible_operators:
            self.operator = value[0]
            value = value[1:]
        else:
            self.operator = ''

        # Strip leading and trailing commas
        value = value.strip(',')

        # Split value into a comma seperated list
        self.fields = value.split(',')

        # Strip whitespaces from each field
        self.fields = map(lambda x: x.strip(), self.fields)


    def __str__(self):
        return self.operator + ','.join(self.fields)

    def __repr__(self):
        return self.__str__()

    def insert(self, index, object):
        """ Same as list.insert()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.insert(1, 'group4')
        >>> print i.fields
        ['group1', 'group4', 'group2', 'group3']

        """
        return self.fields.insert(index,object)

    def append(self, object):
        """ Same as list.append()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.append('group5')
        >>> print i.fields
        ['group1', 'group2', 'group3', 'group5']

        """
        return self.fields.append(object)

    def count(self, value):
        """ Same as list.count()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.count('group3')
        1
        """
        return self.fields.count(value)

    def extend(self, iterable):
        """ Same as list.extend()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.extend(['group4', 'group5'])
        >>> print i.fields
        ['group1', 'group2', 'group3', 'group4', 'group5']
        """
        return self.fields.extend(iterable)

    def index(self, value, start=0, stop=None):
        """ Same as list.index()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.index('group2')
        1
        >>> i.index('group3', 2, 5)
        2

        """
        if stop is None:
            stop = len(self.fields)
        return self.fields.index(value, start, stop)

    def reverse(self):
        """ Same as list.reverse()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.reverse()
        >>> print i.fields
        ['group3', 'group2', 'group1']

        """

        return self.fields.reverse()

    def sort(self):
        """ Same as list.sort()

        >>> i = AttributeList('group3,group1,group2')
        >>> i.sort()
        >>> print i.fields
        ['group1', 'group2', 'group3']


        """
        return self.fields.sort()

    def remove(self, value):
        """ Same as list.remove()

        >>> i = AttributeList('group1,group2,group3')
        >>> i.remove('group3')
        >>> print i.fields
        ['group1', 'group2']

        """
        return self.fields.remove(value)
    def __iter__(self):
        """ Same as list.__iter__()

        >>> mylist = AttributeList('group1,group2,group3')
        >>> for i in mylist: print i
        group1
        group2
        group3
        """
        return self.fields.__iter__()

class PluginOutput:
    """ This class parses a typical stdout from a nagios plugin

    It splits the output into the following fields:
    * Summary
    * Long Output
    * Perfdata

    Example UsagE:
    >>> p = PluginOutput("Everything is ok | load1=15 load2=10")
    >>> p.summary
    'Everything is ok '
    >>> p.long_output
    ''
    >>> p.perfdata
    'load1=15 load2=10'
    >>> p.parsed_perfdata.metrics
    ['load1'=15;;;;, 'load2'=10;;;;]

    """
    summary = None
    long_output = None
    perfdata = None
    def __init__(self, stdout):
        if not stdout:
            return
        long_output = []
        perfdata = []
        summary = None

        lines = stdout.splitlines()
        for i in lines:
            i = i.split('|',1)
            if summary is None:
                summary = i.pop(0)
            else:
                long_output.append(i.pop(0))
            if i:
                perfdata.append(i.pop())
        perfdata = ' '.join(perfdata)

        self.summary = summary
        self.long_output = '\n'.join(long_output)
        self.perfdata = perfdata.strip()
        self.parsed_perfdata = PerfData(perfdatastring=perfdata)




class defaultdict(dict):
    """ This is an alternative implementation of collections.defaultdict.

    Used as a fallback if using python 2.4 or older.

    Usage:
    try:
        from collections import defaultdict
    except ImportError:
        from pynag.Utils import defaultdict
    """
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
            not hasattr(default_factory, '__call__')):
            raise TypeError('first argument must be callable')
        dict.__init__(self, *a, **kw)
        self.default_factory = default_factory
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value
    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()
    def copy(self):
        return self.__copy__()
    def __copy__(self):
        return type(self)(self.default_factory, self)
    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
            copy.deepcopy(self.items()))
    def __repr__(self):
        return 'defaultdict(%s, %s)' % (self.default_factory,
                                        dict.__repr__(self))

