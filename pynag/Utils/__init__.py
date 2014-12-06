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
import threading
from os import getenv, environ, listdir, path
from platform import node
import datetime
import pynag.Plugins
import sys

from pynag.Utils import errors

rlock = threading.RLock()




def runCommand(command, raise_error_on_fail=False, shell=True, env=None):
    """ Run command from the shell prompt. Wrapper around subprocess.

    Args:

        command (str): string containing the command line to run

        raise_error_on_fail (bool): Raise PynagError if returncode > 0

    Returns:

        str: stdout/stderr of the command run

    Raises:

        PynagError if returncode > 0
    """
    run_env = environ.copy()
    # Merge dict into environ
    if env:
        run_env.update(env)
    proc = subprocess.Popen(command,
                            shell=shell,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=run_env)
    stdout, stderr = proc.communicate('through stdin to stdout')
    result = proc.returncode, stdout, stderr
    if proc.returncode > 0 and raise_error_on_fail:
        error_string = "* Could not run command (return code= %s)\n" % proc.returncode
        error_string += "* Error was:\n%s\n" % (stderr.strip())
        error_string += "* Command was:\n%s\n" % command
        error_string += "* Output was:\n%s\n" % (stdout.strip())
        if proc.returncode == 127:  # File not found, lets print path
            path = getenv("PATH")
            error_string += "Check if y/our path is correct: %s" % path
        raise PynagError(error_string)
    else:
        return result





def grep(objects, **kwargs):
    """ Returns all the elements from array that match the keywords in **kwargs

    See documentation for pynag.Model.ObjectDefinition.objects.filter() for
    example how to use this.

    Arguments:

        objects (list of dict): list to be searched

        kwargs (str): Any search argument provided will be checked against every dict

    Examples::

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
    for k, v in kwargs.items():
        # We need the actual array in "v" for __in and __notin
        if isinstance(v, type([])) and not (k.endswith('__in') or k.endswith('__notin')):
            for i in v:
                search.append((k, i))
        else:
            search.append((k, v))
    matching_objects = objects
    for k, v in search:
        #v = str(v)
        v_str = str(v)
        if k.endswith('__contains'):
            k = k[:-len('__contains')]
            expression = lambda x: x.get(k) and v_str in str(x.get(k))
        elif k.endswith('__notcontains'):
            k = k[:-len('__notcontains')]
            expression = lambda x: not v_str in str(x.get(k))
        elif k.endswith('__startswith'):
            k = k[:-len('__startswith')]
            expression = lambda x: str(x.get(k)).startswith(v_str)
        elif k.endswith('__notstartswith'):
            k = k[:-len('__notstartswith')]
            expression = lambda x: not str(x.get(k)).startswith(v_str)
        elif k.endswith('__endswith'):
            k = k[:-len('__endswith')]
            expression = lambda x: str(x.get(k)).endswith(v_str)
        elif k.endswith('__notendswith'):
            k = k[:-len('__notendswith')]
            expression = lambda x: not str(x.get(k)).endswith(v_str)
        elif k.endswith('__exists'):
            k = k[:-len('__exists')]
            expression = lambda x: str(k in x) == v_str
        elif k.endswith('__isnot'):
            k = k[:-len('__isnot')]
            expression = lambda x: v_str != str(x.get(k))
        elif k.endswith('__regex'):
            k = k[:-len('__regex')]
            regex = re.compile(str(v))
            expression = lambda x: regex.search(str(x.get(k)))
        elif k.endswith('__in'):
            k = k[:-len('__in')]
            expression = lambda x: str(x.get(k)) in v
        elif k.endswith('__notin'):
            k = k[:-len('__notin')]
            expression = lambda x: str(x.get(k)) not in v
        elif k.endswith('__has_field'):
            k = k[:-len('__has_field')]
            expression = lambda x: v_str in AttributeList(x.get(k)).fields
        elif k == 'register' and str(v) == '1':
            # in case of register attribute None is the same as "1"
            expression = lambda x: x.get(k) in (v, None)
        elif k in ('search', 'q'):
            expression = lambda x: v_str in str(x)
        else:
            # If all else fails, assume they are asking for exact match
            v_is_str = isinstance(v, str)
            expression = lambda obj: (lambda objval: str(objval) == v_str or (v_is_str and isinstance(objval, list) and v in objval))(obj.get(k))
        matching_objects = filter(expression, matching_objects)
    return matching_objects


def grep_to_livestatus(*args, **kwargs):
    """ Converts from pynag style grep syntax to livestatus filter syntax.

    Example:

        >>> grep_to_livestatus(host_name='test')
        ['Filter: host_name = test']
        >>> grep_to_livestatus(service_description__contains='serv')
        ['Filter: service_description ~ serv']
        >>> grep_to_livestatus(service_description__isnot='serv')
        ['Filter: service_description != serv']
        >>> grep_to_livestatus(service_description__contains=['serv','check'])
        ['Filter: service_description ~ serv']
        >>> grep_to_livestatus(service_description__contains='foo', contacts__has_field='admin')
        ['Filter: contacts >= admin', 'Filter: service_description ~ foo']
        >>> grep_to_livestatus(service_description__has_field='foo')
        ['Filter: service_description >= foo']
        >>> grep_to_livestatus(service_description__startswith='foo')
        ['Filter: service_description ~ ^foo']
        >>> grep_to_livestatus(service_description__endswith='foo')
        ['Filter: service_description ~ foo$']
    """

    result = list(args)  # Args go unchanged back into results
    for k, v in kwargs.items():
        if isinstance(v, list) and len(v) > 0:
            v = v[0]
        if k.endswith('__contains'):
            k = k[:-len('__contains')]
            my_string = "Filter: %s ~ %s" % (k, v)
        elif k.endswith('__has_field'):
            k = k[:-len('__has_field')]
            my_string = "Filter: %s >= %s" % (k, v)
        elif k.endswith('__isnot'):
            k = k[:-len('__isnot')]
            my_string = "Filter: %s != %s" % (k, v)
        elif k.endswith('__startswith'):
            k = k[:-len('__startswith')]
            my_string = "Filter: %s ~ ^%s" % (k, v)
        elif k.endswith('__endswith'):
            k = k[:-len('__endswith')]
            my_string = "Filter: %s ~ %s$" % (k, v)
        elif k == 'WaitObject':
            my_string = "WaitObject: %s" % (v,)
        elif k == 'WaitCondition':
            my_string = "WaitCondition: %s" % (v,)
        elif k == 'WaitTrigger':
            my_string = "WaitTrigger: %s" % (v,)
        elif k == 'WaitTimeout':
            my_string = "WaitTimeout: %s" % (v,)
        elif k in ('Limit', 'limit'):
            my_string = "Limit: %s" % (v,)
        elif k in ('Filter', 'filter'):
            my_string = "Filter: %s" % (v,)
        else:
            my_string = "Filter: %s = %s" % (k, v)
        result.append(my_string)
    return result


class AttributeList(object):

    """ Parse a list of nagios attributes into a parsable format.
    (e. contact_groups)

    This makes it handy to mangle with nagios attribute values that are in a
    comma seperated format.

    Typical comma-seperated format in nagios configuration files looks something
    like this::

        contact_groups     +group1,group2,group3

    Example::

        >>> i = AttributeList('+group1,group2,group3')
        >>> i.operator
        '+'
        >>> i.fields
        ['group1', 'group2', 'group3']

        # if your data is already in a list format you can use it directly:
        >>> i = AttributeList(['group1', 'group2', 'group3'])
        >>> i.fields
        ['group1', 'group2', 'group3']

        # white spaces will be stripped from all fields
        >>> i = AttributeList('+group1, group2')
        >>> i
        +group1,group2
        >>> i.fields
        ['group1', 'group2']

    """

    def __init__(self, value=None):
        self.operator = ''
        self.fields = []

        # this is easy to do if attribue_name is unset
        if not value or value == 'null':
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
        """  Same as list.insert()

        Args:

            object: Any object that will be inserted into self.fields (usually a string)

        Example::

            >>> i = AttributeList('group1,group2,group3')
            >>> i.insert(1, 'group4')
            >>> i.fields
            ['group1', 'group4', 'group2', 'group3']
        """

        return self.fields.insert(index, object)

    def append(self, object):
        """ Same as list.append():

        Args:

            object: Item to append into self.fields (typically a string)


        Example:

            >>> i = AttributeList('group1,group2,group3')
            >>> i.append('group5')
            >>> i.fields
            ['group1', 'group2', 'group3', 'group5']
        """
        return self.fields.append(object)

    def count(self, value):
        """  Same as list.count()

        Args:
            value: Any object that might exist in self.fields (string)

        Returns:
            The number of occurances that 'value' has in self.fields

        Example:
            >>> i = AttributeList('group1,group2,group3')
            >>> i.count('group3')
            1
        """

        return self.fields.count(value)

    def extend(self, iterable):
        """ Same as list.extend()

        Args:
            iterable:   Any iterable that list.extend() supports

        Example:
            >>> i = AttributeList('group1,group2,group3')
            >>> i.extend(['group4', 'group5'])
            >>> i.fields
            ['group1', 'group2', 'group3', 'group4', 'group5']
        """
        return self.fields.extend(iterable)

    def index(self, value, start=0, stop=None):
        """ Same as list.index()

        Args:
            value:  object to look for in self.fields

            start:  start at this index point

            stop:   stop at this index point

        Returns:
            The index of 'value' (integer)

        Examples:
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
        """  Same as list.reverse()

        Examples:
            >>> i = AttributeList('group1,group2,group3')
            >>> i.reverse()
            >>> i.fields
            ['group3', 'group2', 'group1']
        """

        return self.fields.reverse()

    def sort(self):
        """ Same as list.sort()

        Examples:
            >>> i = AttributeList('group3,group1,group2')
            >>> i.sort()
            >>> print(i.fields)
            ['group1', 'group2', 'group3']
        """

        return self.fields.sort()

    def remove(self, value):
        """ Same as list.remove()

        Args:
            value:  The object that is to be removed

        Examples:
            >>> i = AttributeList('group1,group2,group3')
            >>> i.remove('group3')
            >>> i.fields
            ['group1', 'group2']
        """

        return self.fields.remove(value)

    def __iter__(self):
        """ Same as list.__iter__()

        >>> mylist = AttributeList('group1,group2,group3')
        >>> for i in mylist: print(i)
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

    Attributes:

        summary (str): Summary returned by the plugin check

        long_output (str)

        perfdata (str): Data returned by the plugin as a string

        parsed_perfdata: perfdata parsed and split

    Example Usage:

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
    summary = None  # : str. Summary returned by the plugin check
    long_output = None
    perfdata = None  # : str. Data returned by the plugin as a string
    parsed_perfdata = None  # : Perfdata parsed and split

    def __init__(self, stdout):
        if not stdout:
            return
        long_output = []
        perfdata = []
        summary = None

        lines = stdout.splitlines()
        for i in lines:
            i = i.split('|', 1)
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

    Usage::

        try:
            from collections import defaultdict
        except ImportError:
            from pynag.Utils import defaultdict
    """

    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and not hasattr(default_factory, '__call__')):
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
        return type(self)(self.default_factory, copy.deepcopy(self.items()))

    def __repr__(self):
        return 'defaultdict(%s, %s)' % (self.default_factory,
                                        dict.__repr__(self))


def reconsile_threshold(threshold_range):
    """ Take threshold string as and normalize it to the format supported by plugin
    development team

    The input (usually a string in the form of 'the new threshold syntax') is a
    string in the form of x..y

    The output will be a compatible string in the older nagios plugin format
    @x:y

    Examples:

    >>> reconsile_threshold("0..5")
    '@0:5'
    >>> reconsile_threshold("inf..5")
    '5:'
    >>> reconsile_threshold("5..inf")
    '~:5'
    >>> reconsile_threshold("inf..inf")
    '@~:'
    >>> reconsile_threshold("^0..5")
    '0:5'
    >>> reconsile_threshold("10..20")
    '@10:20'
    >>> reconsile_threshold("10..inf")
    '~:10'
    """

    threshold_range = str(threshold_range)
    if not '..' in threshold_range:
        return threshold_range
    threshold_range = threshold_range.strip()
    if threshold_range.startswith('^'):
        operator = ''
        threshold_range = threshold_range[1:]
    else:
        operator = '@'

    start, end = threshold_range.split('..', 1)
    start = start.replace('-inf', '~').replace('inf', '~')
    end = end.replace('-inf', '').replace('inf', '')

    if not start:
        start = '0'

    # Lets convert the common case of @0:x into x:
    if operator == '@' and start == '~' and end not in ('', '~'):
        result = "%s:" % end
    # Convert the common case of @x: into 0:x
    elif operator == '@' and end in ('', '~') and start != '~':
        result = '~:%s' % start
    else:
        result = '%s%s:%s' % (operator, start, end)
    #result = '%s%s:%s' % (operator, start, end)
    return result


def synchronized(lock):
    """ Synchronization decorator

    Use this to make a multi-threaded method synchronized and thread-safe.

    Use the decorator like so::

        @pynag.Utils.synchronized(pynag.Utils.rlock)
    """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        newFunction.__name__ = f.__name__
        newFunction.__module__ = f.__module__
        return newFunction
    return wrap


def cache_only(func):
    def wrap(*args, **kwargs):
        pynag.Model.ObjectFetcher._cache_only = True
        try:
            return func(*args, **kwargs)
        finally:
            pynag.Model.ObjectFetcher._cache_only = False
    wrap.__name__ = func.__name__
    wrap.__module__ = func.__module__
    return wrap


def is_macro(macro):
    """Test if macro is in the format of a valid nagios macro.

    Args:
        macro: String. Any macro, example $HOSTADDRESS$

    Returns:
        Boolean. True if macro is in the format of a macro, otherwise false.

    Examples:
        >>> is_macro('$HOSTADDRESS$')
        True
        >>> is_macro('$HOSTADDRESS')
        False
        >>> is_macro('')
        False
        >>> is_macro('$CONTACTNAME$')
        True
        >>> is_macro('$SERVICEDESC$')
        True
        >>> is_macro('$_SERVICE_CUSTOM$')
        True
        >>> is_macro('$_HOST_CUSTOM$')
        True
        >>> is_macro('$_CONTACT_CUSTOM$')
        True
    """
    if not macro.startswith('$'):
        return False
    if not macro.endswith('$'):
        return False

    # Remove $ from macro
    macro = macro[1:-1]
    if not macro:
        return False
    return True


# These are here for backwards compatibility only
from pynag.Utils import checkresult
from pynag.Utils import metrics
from pynag.Utils import git
from pynag.Utils import nsca

PerfData = metrics.PerfData
PerfDataMetric = metrics.PerfDataMetric
GitRepo = git.GitRepo
CheckResult = checkresult.CheckResult
PynagError = errors.PynagError
send_nsca = nsca.send_nsca