# -*- coding: utf-8 -*-
""" Classes and functions related to Perfdata metrics."""
import shlex
import re
import pynag.Plugins
from pynag.Utils import errors


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
            status = pynag.Plugins.check_threshold(self.value, warning=self.warn, critical=self.crit)
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
        """ Convert threshold from new threshold syntax to current one.

        For backwards compatibility
        """

        self.warn = reconsile_threshold(self.warn)
        self.crit = reconsile_threshold(self.crit)

    def split_value_and_uom(self, value):
        """
        Example:

        get value="10M" and return (10,"M")

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
            return '', ''
        return tmp[0]

    def get_dict(self):
        """ Returns a dictionary which contains this class' attributes.

        Returned dict example::

            {
                'label': self.label,
                'value': self.value,
                'uom': self.uom,
                'warn': self.warn,
                'crit': self.crit,
                'min': self.min,
                'max': self.max,
            }
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
        """ Convert all thresholds in new_threshold_syntax to the standard one """
        for i in self.metrics:
            i.reconsile_thresholds()

    def __str__(self):
        metrics = map(lambda x: x.__str__(), self.metrics)
        return ' '.join(metrics)


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
    return result
