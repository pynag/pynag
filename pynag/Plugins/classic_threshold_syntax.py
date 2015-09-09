# -*- coding: utf-8 -*-
"""Support for classic nagios threshold syntax.

Nagios plugins development team and Monitoring Plugin Development team both
define what the syntax of a threshold should be, and it can be looked up here:
* http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT
* https://www.monitoring-plugins.org/doc/guidelines.html#THRESHOLDFORMAT

"""
import pynag.errors

# Map the return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


class Error(pynag.errors.PynagError):
    """Base class for errors in this module."""


class InvalidThreshold(Error):
    """Raised when an invalid threshold was provided."""


def check_threshold(value, warning=None, critical=None):
    """ Checks value against warning/critical and returns Nagios exit code.

    Format of range_threshold is according to:
    http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT

    Returns (in order of appearance):
        UNKNOWN int(3)  -- On errors or bad input
        CRITICAL int(2) -- if value is within critical threshold
        WARNING int(1)  -- If value is within warning threshold
        OK int(0)       -- If value is outside both thresholds
    Arguments:
        value -- value to check
        warning -- warning range
        critical -- critical range

    # Example Usage:
    >>> check_threshold(88, warning="0:90", critical="0:95")
    0
    >>> check_threshold(92, warning=":90", critical=":95")
    1
    >>> check_threshold(96, warning=":90", critical=":95")
    2
    """
    if critical and not check_range(value, critical):
        return CRITICAL
    elif warning and not check_range(value, warning):
        return WARNING
    else:
        return OK


def check_range(value, range_threshold=None):
    """ Returns True if value is within range_threshold.

    Format of range_threshold is according to:
    http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT

    Arguments:
        value -- Numerical value to check (i.e. 70 )
        range -- Range to compare against (i.e. 0:90 )
    Returns:
        True  -- If value is inside the range
        False -- If value is outside the range (alert if this happens)
        False -- if invalid value is specified

    Summary from plugin developer guidelines:
    ---------------------------------------------------------
    x       Generate an alert if x...
    ---------------------------------------------------------
    10      < 0 or > 10, (outside the range of {0 .. 10})
    10:     < 10, (outside {10 .. ∞})
    ~:10    > 10, (outside the range of {-∞ .. 10})
    10:20   < 10 or > 20, (outside the range of {10 .. 20})
    @10:20  ≥ 10 and ≤ 20, (inside the range of {10 .. 20})
    ---------------------------------------------------------


    # Example runs for doctest, False should mean alert
    >>> check_range(78, "90") # Example disk is 78% full, threshold is 90
    True
    >>> check_range(5, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(0, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(10, 10) # Everything between 0 and 10 is True
    True
    >>> check_range(11, 10) # Everything between 0 and 10 is True
    False
    >>> check_range(-1, 10) # Everything between 0 and 10 is True
    False
    >>> check_range(-1, "~:10") # Everything Below 10
    True
    >>> check_range(11, "10:") # Everything above 10 is True
    True
    >>> check_range(1, "10:") # Everything above 10 is True
    False
    >>> check_range(0, "5:10") # Everything between 5 and 10 is True
    False
    >>> check_range(0, "@5:10") # Everything outside 5:10 is True
    True
    >>> check_range(None) # Return False if value is not a number
    False
    >>> check_range("10000000 PX") # What happens on invalid input
    False
    >>> check_range("10000000", "invalid:invalid") # What happens on invalid range
    Traceback (most recent call last):
    ...
    InvalidThreshold: Invalid threshold format: invalid:invalid
    """

    # Return false if value is not a number
    try:
        float(value)
    except Exception:
        return False

    # if no range_threshold is provided, assume everything is ok
    if not range_threshold:
        range_threshold = '~:'
    range_threshold = str(range_threshold)
    # If range starts with @, then we do the opposite
    if range_threshold[0] == '@':
        return not check_range(value, range_threshold[1:])

    if range_threshold.find(':') > -1:
        (start, end) = (range_threshold.split(':', 1))
    # we get here if ":" was not provided in range_threshold
    else:
        start = ''
        end = range_threshold
    # assume infinity if start is not provided
    if start == '~':
        start = None
    # assume start=0 if start is not provided
    if start == '':
        start = 0
    # assume infinity if end is not provided
    if end == '':
        end = None

    try:
        # start is defined and value is lower than start
        if start is not None and float(value) < float(start):
            return False
        if end is not None and float(value) > float(end):
            return False
    except ValueError:
        raise InvalidThreshold("Invalid threshold format: %s" % range_threshold)
    return True
