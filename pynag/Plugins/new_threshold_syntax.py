# -*- coding: utf-8 -*-
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

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import pynag.Plugins
import pynag.errors
from pynag.Utils import states

class Error(pynag.errors.PynagError):
    """Base class for errors in this module."""


class InvalidThreshold(Error):
    """Raised when an invalid threshold was provided."""


def check_threshold(value, ok=None, warning=None, critical=None):
    """ Checks value against warning/critical and returns Nagios exit code.

    Format of range_threshold is according to:
    http://nagiosplugins.org/rfc/new_threshold_syntax

    This function returns (in order of appearance):
        int(0) - If no levels are specified, return OK
        int(3) - If any invalid input provided, return UNKNOWN
        int(0) - If an ok level is specified and value is within range, return OK
        int(2) - If a critical level is specified and value is within range, return CRITICAL
        int(1) - If a warning level is specified and value is within range, return WARNING
        int(2) - If an ok level is specified, return CRITICAL
        int(0) - Otherwise return OK

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
    try:
        # 1 - If no levels are specified, return OK
        if not ok and not warning and not critical:
            return states.OK
        # 2 - If an ok level is specified and value is within range, return OK
        if ok and check_range(value, ok):
            return states.OK
        # 3 - If a critical level is specified and value is within range, return CRITICAL
        if critical and check_range(value, critical):
            return states.CRITICAL
        # 4 - If a warning level is specified and value is within range, return WARNING
        if warning and check_range(value, warning):
            return states.WARNING
        # 5 - If an ok level is specified, return CRITICAL
        if ok:
            return states.CRITICAL
        # 6 - Otherwise return OK
        return states.OK
    except Exception:
        # Return unknown if any problem occurs, including invalid input
        return states.UNKNOWN


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

    if not isinstance(range, basestring) or range == '':
        raise InvalidThreshold('range must be a string')

    # value must be numeric, so we try to convert it to float
    value = float(value)

    # If range does not contain ".." then we assume its the older style of
    # ranges (either a plain number or the start:end syntax)
    if '..' not in range:
        return not pynag.Plugins.classic_threshold_syntax.check_range(value=value, range_threshold=range)
    # If range starts with ^ we the conditions are inverted
    if range[0] == '^':
        return not check_range(value, range[1:])

    # Start and end must be defined
    tmp = range.split('..')
    if len(tmp) != 2:
        raise InvalidThreshold('Invalid Format for threshold range: "%s"' % range)
    start, end = tmp

    if not start in ('inf', '-inf'):
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
        >>> parse_threshold('metric=disk_usage,ok=0..90,warning=90..95,critical=95.100')
        {'thresholds': [(0, '0..90'), (1, '90..95'), (2, '95.100')], 'metric': 'disk_usage'}
    """
    tmp = threshold.lower().split(',')
    parsed_thresholds = []
    results = {}
    results['thresholds'] = parsed_thresholds
    for i in tmp:
        if i.find('=') < 1:
            raise InvalidThreshold("Invalid input: '%s' is not of the format key=value" % i)
        key, value = i.split('=', 1)
        if key in pynag.Plugins.state.keys():
            parsed_thresholds.append((pynag.Plugins.state[key], value))
        else:
            results[key] = value
    return results


def convert_to_classic_format(threshold_range):
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
    return result

