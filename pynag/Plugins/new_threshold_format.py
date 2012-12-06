1# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2012 Pall Sigurdsson
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
These are helper functions and implementation of proposed new threshold format for nagios plugins
according to: http://nagiosplugins.org/rfc/new_threshold_syntax

In short, plugins should implement a --threshold option which takes argument in form of:
  # metric={metric},ok={range},warn={range},crit={range},unit={unit}prefix={SI prefix}

Example:
  --treshold metric=load1,ok=0..5,warning=5..10,critical=10..inf

"""
import pynag.Plugins
from pynag.Utils import PynagError


def check_threshold(value, ok=None, warning=None, critical=None):
    """ Checks value against warning/critical and returns Nagios exit code.

    Format of range_threshold is according to:
    http://nagiosplugins.org/rfc/new_threshold_syntax

    Returns (in order of appearance):
        UNKNOWN int(3)  -- On errors or bad input
        OK int(0)       -- If value is within ok threshold
        CRITICAL int(2) -- if value is within critical threshold
        WARNING int(1)  -- If value is within warning threshold
        OK int(0)       -- If value is outside both warning and critical
        OK int(0)       -- If no thresholds are provided
    Arguments:
        value    -- value to check
        ok       -- ok range
        warning  -- warning range
        critical -- critical range

    # Example Usage:
    >>> check_threshold(88, warning="90..95", critical="95..100")
    0
    >>> check_threshold(92, warning="90..95", critical="95..100")
    1
    >>> check_threshold(96, warning="90..95", critical="95..100")
    2
    """
    if ok and check_range(value, ok):
        return OK
    elif critical and check_range(value, critical):
        return CRITICAL
    elif warning and check_range(value, warning):
        return WARNING
    else:
        return OK


def check_range(value, range):
    """ Returns True if value is within range, else False

    Arguments:
      value -- Numerical value to check, can be any number
      range -- string in the format of "start..end"
    Examples:
    >>> check_range(5, "0..10")
    True
    >>> check_range(11, "0..10")
    False
    """

    if not type(range) == type('') or range == '':
        raise PynagError('range must be a string')
        # value must be numeric, so we try to convert it to float
    value = float(value)

    # If range starts with ^ we the conditions are inverted
    if range[0] == '^':
        return not check_range(value, range[1:])

    # Start and end must be defined
    tmp = range.split('..')
    if len(tmp) != 2:
        raise PynagError('Invalid Format for threshold range: "%s"' % range)
    start,end = tmp

    if not start in ('inf','-inf'):
        start = float(start)
        if start > value:
            return False
    if not end == 'inf':
        end = float(end)
        if end < value:
            return False
    return True


def parse_threshold(threshold):
    """ takes a threshold string as an input and returns a hash map of options and values

    Examples:
        >>> parse_threshold('metric=disk_usage,ok=0..90,warning=90..95,critical=95.100")
        {'metric':'disk_usage', 'thresholds':[(0,'0..90'), (1,'90..95'),(2,'95..100')]}
    """
    tmp = threshold.lower().split(',')
    parsed_thresholds = []
    metric_name=None
    results = {}
    results['thresholds'] = parsed_thresholds
    for i in tmp:
        if i.find('=') < 1:
            raise PynagError("Invalid input: '%s' is not of the format key=value" % i)
        key,value = i.split('=',1)
        if key in pynag.Plugins.state.keys():
            parsed_thresholds.append( (pynag.Plugins.state[key], value) )
        else:
            results[key] = value
    return results
