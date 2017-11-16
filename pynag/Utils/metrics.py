# -*- coding: utf-8 -*-
""" Classes and functions related to Perfdata metrics."""
from __future__ import absolute_import
import shlex
import re
from pynag import errors
from pynag.Plugins import new_threshold_syntax
from pynag.Plugins import classic_threshold_syntax
from six.moves import map


MULTIPLIERS = {
    'h': 10**2,
    'k': 10**3,
    'M': 10**6,
    'G': 10**9,
    'T': 10**12,
    'P': 10**15,
    'E': 10**18,
    'Z': 10**21,
    'Y': 10**24,

    'kB': 1000,
    'MB': 1000**2,
    'GB': 1000**3,
    'TB': 1000**4,
    'PB': 1000**5,
    'EB': 1000**6,
    'ZB': 1000**7,
    'YB': 1000**8,

    'kiB': 1024,
    'MiB': 1024**2,
    'GiB': 1024**3,
    'TiB': 1024**4,
    'PiB': 1024**5,
    'EiB': 1024**6,
    'ZiB': 1024**7,
    'YiB': 1024**8,
}


class PerfDataMetric(object):

    """ Data structure for one single Nagios Perfdata Metric


    Attributes:

        perfdatastring (str): Complete perfdata string

        label (str): Label section of the perfdata string

        value (str): Value section of the perfdata string

        warn (str): WARNING threshold

        crit (str): CRITICAL threshold

        min (str): Minimal value of control

        max (str): Maximal value of control

        uom (str): Measure unit (octets, bits/s, volts, ...)

    """

    label = ""  # : str. Label section of the perfdata string
    value = ""  # : str. Value section of the perfdata string
    warn = ""  # : str. WARNING threshold
    crit = ""  # : str CRITICAL threshold
    min = ""  # : str. Minimal value of control
    max = ""  # : str. Maximal value of control
    uom = ""  # : str. Measure unit (octets, bits/s, volts, ...)

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

    def __init__(self, perfdatastring="", label="", value="", warn="", crit="", min="", max="", uom=""):
        """
        >>> p = PerfData(perfdatastring="size=10M;20M;;;")
        >>> metric = p.get_perfdatametric('size')
        >>> print(metric.label)
        size
        >>> print(metric.value)
        10
        >>> print(metric.uom)
        M
        >>> p = PerfDataMetric(perfdatastring="'with spaces'=10")
        >>> print(p.label)
        with spaces
        >>> print(p.value)
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

        # Hack: For some weird reason livestatus sometimes delivers perfdata in
        # utf-32 encoding.
        perfdatastring = perfdatastring.replace('\x00', '')
        if len(perfdatastring) == 0:
            return

        # If label is single quoted, there might be any symbol in the label
        # including other single quotes and the = sign. Therefore, we take
        # special precautions if it is so
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
            self.value, self.uom = split_value_and_uom(val)
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

        Example:

        self.value with self.warn and self.crit

        >>> PerfDataMetric("label1=10;20;30").get_status()
        0
        >>> PerfDataMetric("label2=25;20;30").get_status()
        1
        >>> PerfDataMetric("label3=35;20;30").get_status()
        2

        Invalid metrics always return unknown

        >>> PerfDataMetric("label3=35;invalid_metric").get_status()
        3
        """

        try:
            status = classic_threshold_syntax.check_threshold(self.value, warning=self.warn, critical=self.crit)
        except errors.PynagError:
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
        >>> PerfDataMetric("value=5.5").is_valid()
        True
        >>> PerfDataMetric("value=5,5").is_valid()
        True
        """

        if self.label in (None, ''):
            return False

        if self.value in (None, ''):
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

    def reconsile_thresholds(self):
        """ Convert threshold from new threshold syntax to classic.

        For backwards compatibility

        Example:
            >>> p = PerfDataMetric(warn='0..100')
            >>> p.warn
            '0..100'
            >>> p.reconsile_thresholds()
            >>> p.warn
            u'@0:100'

        """

        self.warn = new_threshold_syntax.convert_to_classic_format(self.warn)
        self.crit = new_threshold_syntax.convert_to_classic_format(self.crit)

    def get_dict(self):
        """ Returns a dictionary which contents this class' attributes.

        Returns:
            Dict. With every key as a string, and every value is a string.
            {
                'label': self.label,
                'value': self.value,
                'uom': self.uom,
                'warn': self.warn,
                'crit': self.crit,
                'min': self.min,
                'max': self.max,
            }

        Examples:
            >>> p = PerfDataMetric("load=5")
            >>> p.get_dict()
            {'min': '', 'max': '', 'value': '5', 'label': 'load', 'warn': '', 'crit': '', 'uom': ''}
        """

        return {
            'label': self.label,
            'value': self.value,
            'uom': self.uom,
            'warn': self.warn,
            'crit': self.crit,
            'min': self.min,
            'max': self.max,
        }

    def get_base_value(self):
        """Get the base value for current metric.

        This is a simple convenience wrapper around get_base_value()
        module function.

        Returns:
            float. Base value of self.value after unit of measurement
            has been taken into account.

        Examples:
            >>> p = PerfDataMetric('size=10KiB')
            >>> p.get_base_value()
            10240.0
        """
        return get_base_value(self.value, self.uom, self.max)


class PerfData(object):

    """ Data Structure for a nagios perfdata string with multiple perfdata metric

    Example string:

    >>> perf = PerfData("load1=10 load2=10 load3=20 'label with spaces'=5")
    >>> perf.metrics
    ['load1'=10;;;;, 'load2'=10;;;;, 'load3'=20;;;;, 'label with spaces'=5;;;;]
    >>> for i in perf.metrics: print("%s %s" % (i.label, i.value))
    load1 10
    load2 10
    load3 20
    label with spaces 5
    """

    def __init__(self, perfdatastring=""):
        """
        >>> perf = PerfData("load1=10 load2=10 load3=20")
        """
        self.metrics = []
        self.invalid_metrics = []
        # Hack: For some weird reason livestatus sometimes delivers perfdata in
        # utf-32 encoding.
        perfdatastring = perfdatastring.replace('\x00', '')
        try:
            perfdata = shlex.split(perfdatastring)
            for metric in perfdata:
                try:
                    self.add_perfdatametric(metric)
                except Exception:
                    self.invalid_metrics.append(metric)
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

    def add_perfdatametric(self, perfdatastring="", label="", value="", warn="", crit="", min="", max="", uom=""):
        """ Add a new perfdatametric to existing list of metrics.

        Args:

            perfdatastring (str): Complete perfdata string

            label (str): Label section of the perfdata string

            value (str): Value section of the perfdata string

            warn (str): WARNING threshold

            crit (str): CRITICAL threshold

            min (str): Minimal value of control

            max (str): Maximal value of control

            uom (str): Measure unit (octets, bits/s, volts, ...)

        Example:

        >>> s = PerfData()
        >>> s.add_perfdatametric("a=1")
        >>> s.add_perfdatametric(label="utilization",value="10",uom="%")
        """
        metric = PerfDataMetric(perfdatastring=perfdatastring, label=label, value=value, warn=warn, crit=crit, min=min, max=max, uom=uom)
        self.metrics.append(metric)

    def get_perfdatametric(self, metric_name):
        """ Get one specific perfdatametric

        Args:
            metric_name (str): Name of the metric to return

        Example:

        >>> s = PerfData("cpu=90% memory=50% disk_usage=20%")
        >>> my_metric = s.get_perfdatametric('cpu')
        >>> my_metric.label, my_metric.value
        ('cpu', '90')
        """
        for i in self.metrics:
            if i.label == metric_name:
                return i

    def reconsile_thresholds(self):
        """Convert all warn and crit thresholds into classic thresholds format.

        Example:
            >>> p = PerfData('load=15;0..5;;;')
            >>> print p
            'load'=15;0..5;;;
            >>> p.reconsile_thresholds()
            >>> print p
            'load'=15;@0:5;;;

        """
        for i in self.metrics:
            i.reconsile_thresholds()

    def __str__(self):
        """ Simple string representation of our PerfData.

        Example:
            >>> p = PerfData('load=15')
            >>> str(p)
            "'load'=15;;;;"

        """
        metrics = [x.__str__() for x in self.metrics]
        return ' '.join(metrics)


def split_value_and_uom(value):
    """split_value_and_uom("10mb") -> ('10', 'mb')

    Args:
        value: String. Usually a perfdata metric like '10mb'

    Returns:
        A tuple of ('str', 'str') e.g. ('10', 'mb')

    Examples:
        >>> split_value_and_uom( "10" )
        ('10', '')
        >>> split_value_and_uom( "10c" )
        ('10', 'c')
        >>> split_value_and_uom( "10B" )
        ('10', 'B')
        >>> split_value_and_uom( "10MB" )
        ('10', 'MB')
        >>> split_value_and_uom( "10KB" )
        ('10', 'KB')
        >>> split_value_and_uom( "10TB" )
        ('10', 'TB')
        >>> split_value_and_uom( "10%" )
        ('10', '%')
        >>> split_value_and_uom( "10s" )
        ('10', 's')
        >>> split_value_and_uom( "10us" )
        ('10', 'us')
        >>> split_value_and_uom( "10ms" )
        ('10', 'ms')

    """
    tmp = re.findall(r"([-]*[\d.]*\d+)(.*)", value)
    if len(tmp) == 0:
        return '', ''
    return tmp[0]


def get_base_value(value, uom=None, maximum=None):
    """ Get base value of a metric (i.e. turns 1KB into 1024).

    Examples:
        >>> get_base_value(value=50)
        50.0
        >>> get_base_value(value=1, uom='kib')
        1024.0
        >>> get_base_value(value=1, uom='k')
        1000.0
        >>> get_base_value(value=1, uom='kb')
        1000.0
        >>> get_base_value(value=1, uom='gib')
        1073741824.0
        >>> get_base_value(value=1, uom='g')
        1000000000.0
        >>> get_base_value(value=50, uom='%', maximum=10)
        5.0
        >>> get_base_value(value=50, uom='%')
        Traceback (most recent call last):
          ...
        ValueError: Cant get absolute value for 50% unless max is defined.
        >>> get_base_value(value=50, uom='FOO')
        Traceback (most recent call last):
          ...
        ValueError: Dont know how to get the base value of a "FOO".

    Returns:
        float. Base value of self.value after uom has been taken into account.
    """
    float_value = float(value)
    all_multipliers_in_lowercase = {}
    for key, multiplier in MULTIPLIERS.items():
        all_multipliers_in_lowercase[key.lower()] = multiplier
    if not uom:
        return float_value
    elif uom == '%' and not maximum:
        raise ValueError('Cant get absolute value for %s%s unless max is defined.' % (value, uom))
    elif uom == '%':
        return float_value * 0.01 * float(maximum)
    elif uom in MULTIPLIERS:
        return float_value * MULTIPLIERS[uom]
    elif uom.lower() in all_multipliers_in_lowercase:
        return float_value * all_multipliers_in_lowercase[uom.lower()]
    else:
        raise ValueError('Dont know how to get the base value of a "%s".' % uom)
