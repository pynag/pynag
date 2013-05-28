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

"""
Python Nagios extensions
"""

import sys
import os
import traceback
from platform import node
from optparse import OptionParser, OptionGroup
from pynag.Utils import PerfData
import new_threshold_syntax

# Map the return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

ok,warning,critical,unknown = 0,1,2,3

state = {}
state['ok'] = 0
state['warning'] = 1
state['warn'] = 1
state['w'] = 1
state['critical'] = 2
state['crit'] = 2
state['c'] = 2
state['unknown'] = 3
state['u'] = 3
state['UP'] = 0
state['DOWN'] = 2
state['UNREACHABLE'] = 2
state['OK'] = 0
state['WARNING'] = 1
state['CRITICAL'] = 2
state['UNKNOWN'] = 3

state_text = {}
state_text[ok] = 'OK'
state_text[warning] = 'Warning'
state_text[critical] = "Critical"
state_text[unknown] = "Unknown"

class simple:
    """
    Nagios plugin helper library based on Nagios::Plugin

    Sample usage

    from pynag.Plugins import WARNING, CRITICAL, OK, UNKNOWN, simple as Plugin

    # Create plugin object
    np = Plugin()
    # Add arguments
    np.add_arg("d", "disk")
    # Do activate plugin
    np.activate()
    ... check stuff, np['disk'] to address variable assigned above...
    # Add a status message and severity
    np.add_message( WARNING, "Disk nearing capacity" )
    # Get parsed code and messages
    (code, message) = np.check_messages()
    # Return information and exit
    nagios_exit(code, message)
    """

    def __init__(self, shortname = None, version = None, blurb = None, extra = None, url = None, license = None, plugin = None, timeout = 15, must_threshold = True):

        ## this is the custom parser
        self.extra_list_optional = []
        self.extra_list_required = []

        ## Set the option parser stuff here
        self.parser = OptionParser()

        ## Variables we'll get later
        self.opts = None
        self.must_threshold = must_threshold
        self.data = {}
        self.data['perfdata'] = []
        self.data['messages'] = { OK:[], WARNING:[], CRITICAL:[], UNKNOWN:[] }
        self.data['threshhold'] = None

        ## Error mappings, for easy access
        self.errors = { "OK":0, "WARNING":1, "CRITICAL":2, "UNKNOWN":3, }
        self.status_text = { 0:"OK", 1:"WARNING", 2:"CRITICAL", 3:"UNKNOWN", }

        ## Shortname creation
        if not shortname:
            self.data['shortname'] = os.path.basename("%s" % sys.argv[0])
        else:
            self.data['shortname'] = shortname

    def add_arg(self, spec_abbr, spec, help_text, required=1, action="store"):
        """
        Add an argument to be handled by the option parser.  By default, the arg is not required.
        
        required = optional parameter
        action = [store, append, store_true]
        """
        self.parser.add_option("-%s" % spec_abbr, "--%s" % spec, dest="%s" % spec, help=help_text, metavar="%s" % spec.upper(), action=action)
        if required:
            self.extra_list_required.append(spec)
        else:
            self.extra_list_optional.append(spec)

    def activate(self):
        """
        Parse out all command line options and get ready to process the plugin.  This should be run after argument preps
        """
        timeout = None
        verbose = 0

        self.parser.add_option("-v", "--verbose", dest="verbose", help="Verbosity Level", metavar="VERBOSE", default=0)
        self.parser.add_option("-H", "--host", dest="host", help="Target Host", metavar="HOST")
        self.parser.add_option("-t", "--timeout", dest="timeout", help="Connection Timeout", metavar="TIMEOUT")

        if self.must_threshold == True:
            self.parser.add_option("-c", "--critical", dest="critical", help="Critical Threshhold", metavar="CRITICAL")
            self.parser.add_option("-w", "--warning", dest="warning", help="Warn Threshhold", metavar="WARNING")

        (options, args) = self.parser.parse_args()

        ## Set verbosity level
        if int(options.verbose) in (0, 1, 2, 3):
            self.data['verbosity'] = int(options.verbose)
        else:
            self.data['verbosity'] = verbose

        ## Ensure the hostname is set
        if options.host:
            self.data['host'] = options.host

        ## Set timeout
        if options.timeout:
            self.data['timeout'] = options.timeout
        else:
            self.data['timeout'] = timeout

        if self.must_threshold == True and not options.critical and not options.warning:
            self.parser.error("You must provide a WARNING and/or CRITICAL value")

        ## Set Critical; if the option is available in the plugin
        if hasattr(options, 'critical'):
            self.data['critical'] = options.critical
        else:
            self.data['critical'] = None

        ## Set Warn; if the option is available in the plugin
        if hasattr(options, 'warning'):
            self.data['warning'] = options.warning
        else:
            self.data['warning'] = None

        ## Ensurethat the extra items are provided
        for extra_item in self.extra_list_required:
            if not options.__dict__[extra_item]:
                self.parser.error("option '%s' is required" % extra_item)


        ## Put the remaining values into the data dictionary
        for key,value in options.__dict__.items():
            if key in (self.extra_list_required + self.extra_list_optional):
                self.data[key] = value

    def add_perfdata(self, label , value , uom = None, warn = None, crit = None, minimum = None, maximum = None):
        """
        Append perfdata string to the end of the message
        """

        # Append perfdata (assume multiple)
        self.data['perfdata'].append({ 'label' : label, 'value' : value, 'uom' : uom, 
            'warn' : warn, 'crit' : crit, 'min' : minimum, 'max' : maximum})

    def check_perfdata_as_metric(self):
        for perfdata in self.data['perfdata']:
            self._add_message_from_range_check(
                perfdata['value'],
                perfdata['warn'],
                perfdata['crit'],
                perfdata['label']
            )

        self._check_messages_and_exit()

    def _add_message_from_range_check(self, value, warning = None, critical = None, label = 'data'):
        if not (critical or warning):
            critical = self.data['critical']
            warning = self.data['warning']

        if critical and not self._range_checker(value, critical):
            self.add_message(CRITICAL,"%s %s is outside critical range: %s" % (label, value, critical))
        elif warning and not self._range_checker(value, warning):
            self.add_message(WARNING,"%s %s is outside warning range: %s" % (label, value, warning))
        else:
            self.add_message(OK,"%s %s is inside warning=%s and critical=%s" % (label, value, warning, critical))

    def _check_messages_and_exit(self):
        # Get all messages appended and exit code
        (code, message) = self.check_messages()

        # Exit with appropriate exit status and message
        self.nagios_exit(code, message)

    def check_range(self, value):
        """
        Check if a value is within a given range.  This should replace change_threshold eventually. Exits with appropriate exit code given the range.

        Taken from:  http://nagiosplug.sourceforge.net/developer-guidelines.html
        Range definition
    
        Generate an alert if x...
        10        < 0 or > 10, (outside the range of {0 .. 10})
        10:        < 10, (outside {10 .. #})
        ~:10    > 10, (outside the range of {-# .. 10})
        10:20    < 10 or > 20, (outside the range of {10 .. 20})
        @10:20    # 10 and # 20, (inside the range of {10 .. 20})
        """
        self.hr_range = ""

        self._add_message_from_range_check(value)
        self._check_messages_and_exit()


    def _range_checker(self, value, range_threshold):
        """ deprecated. Use pynag.Plugins.check_range() """
        return check_range(value=value, range_threshold=range_threshold)

    def send_nsca(self, code, message, ncsahost, hostname=node(), service=None):
        """
        Send data via send_nsca for passive service checks
        """
    
        # Execute send_nsca
        from popen2 import Popen3
        command = "send_nsca -H %s" % ncsahost
        p = Popen3(command,  capturestderr=True)

        # Service check
        if service:
            print >>p.tochild, "%s	%s	%s	%s %s" % (hostname, service, code, message, self.perfdata_string())
        # Host check, omit service_description
        else:
            print >>p.tochild, "%s	%s	%s %s" % (hostname, code, message, self.perfdata_string())

        # Send eof
        # TODO, support multiple statuses ?
        p.tochild.close()

        # Save output incase we have an error
        nsca_output = ''
        for line in p.fromchild.readlines():
            nsca_output += line

        # Wait for send_nsca to exit
        returncode = p.wait()
        returncode = os.WEXITSTATUS( returncode) 

        # Problem with running nsca
        if returncode != 0:
            if returncode == 127:
                raise Exception("Could not find send_nsca in path")
            else:
                raise Exception("returncode: %i\n%s" % (returncode, nsca_output))

        return 0

    def nagios_exit(self, code_text, message):
        """
        Exit with exit_code, message, and optionally perfdata
        """

        # Change text based codes to int
        code = self.code_string2int(code_text)

        ## This should be one line (or more in nagios 3)
        print "%s: %s %s" % (self.status_text[code], message, self.perfdata_string())
        sys.exit(code)

    def perfdata_string(self):

        ## Append perfdata to the message, if perfdata exists
        if self.data['perfdata']:
            append = '|'
        else:
            append = ''

        for pd in self.data['perfdata']:
            append += " '%s'=%s%s;%s;%s;%s;%s" % (
                pd['label'],
                pd['value'],
                pd['uom'] or '',
                pd['warn'] or '',
                pd['crit'] or '',
                pd['min'] or '',
                pd['max'] or '')

        return append

    def add_message( self, code, message ):
        """
        Add a message with code to the object. May be called
        multiple times.  The messages added are checked by check_messages,
        following.

        Only CRITICAL, WARNING, OK and UNKNOWN are accepted as valid codes.
        """
        # Change text based codes to int
        code = self.code_string2int(code)

        self.data['messages'][code].append( message )

    def check_messages( self, joinstr = " ", joinallstr = None ):
        """
        Check the current set of messages and return an appropriate nagios
        return code and/or a result message. In scalar context, returns
        only a return code; in list context returns both a return code and
        an output message, suitable for passing directly to nagios_exit()

        joinstr = string
            A string used to join the relevant array to generate the
            message string returned in list context i.e. if the 'critical'
            array is non-empty, check_messages would return:
                joinstr.join(critical)

        joinallstr = string
            By default, only one set of messages are joined and returned in
            the result message i.e. if the result is CRITICAL, only the
            'critical' messages are included in the result; if WARNING,
            only the 'warning' messages are included; if OK, the 'ok'
            messages are included (if supplied) i.e. the default is to
            return an 'errors-only' type message.

            If joinallstr is supplied, however, it will be used as a string
            to join the resultant critical, warning, and ok messages
            together i.e.  all messages are joined and returned.
        """
        # Check for messages in unknown, critical, warning, ok to determine
        # code
        keys = self.data['messages'].keys()
        keys.sort(reverse=True)
        code = UNKNOWN
        for code in keys:
            if len(self.data['messages'][code]):
                break

        # Create the relevant message for the most severe code
        if joinallstr is None:
            message = joinstr.join(self.data['messages'][code])
        # Join all strings whether OK, WARN...
        else:
            message = ""
            for c in keys:
                if len(self.data['messages'][c]):
                    message += joinallstr.join(self.data['messages'][c]) + joinallstr

        return code, message.rstrip(joinallstr)

    def code_string2int( self, code_text ):
        """
        Changes CRITICAL, WARNING, OK and UNKNOWN code_text to integer
        representation for use within add_message() and nagios_exit()
        """

        # If code_text is a string, convert to the int
        if str(type(code_text)) == "<type 'str'>":
            code = self.errors[code_text]
        else:
            code = code_text

        return code

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None

def check_threshold(value, warning=None, critical=None):
    """ Checks value against warning/critical and returns Nagios exit code.

    Format of range_threshold is according to:
    http://nagiosplug.sourceforge.net/developer-guidelines.html#THRESHOLDFORMAT

    Returns (in order of appearance):
        UNKNOWN int(3)  -- On errors or bad input
        CRITICAL int(2) -- if value is within critical threshold
        WARNING int(1)  -- If value is within warning threshold
        OK int(0)       -- If value is outside both tresholds
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
    10  	< 0 or > 10, (outside the range of {0 .. 10})
    10:     < 10, (outside {10 .. ∞})
    ~:10    > 10, (outside the range of {-∞ .. 10})
    10:20   < 10 or > 20, (outside the range of {10 .. 20})
    @10:20  ≥ 10 and ≤ 20, (inside the range of {10 .. 20})
    10      < 0 or > 10, (outside the range of {0 .. 10})
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
    True
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

    # Return False on invalid value input
    try:
        value = float(value)
    except Exception:
        return False
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
    # start is defined and value is lower than start
    try:
        if start is not None and float(value) < float(start):
            return False
        if end is not None and float(value) > float(end):
            return False
    except ValueError:
        return True
    return True


class PluginHelper:
    """ PluginHelper takes away some of the tedious work of writing Nagios plugins. Primary features include:

    * Keep a collection of your plugin messages (queue for both summary and longoutput)
    * Keep record of exit status
    * Keep a collection of your metrics (for both perfdata and thresholds)
    * Automatic Command-line arguments
    * Make sure output of your plugin is within Plugin Developer Guidelines

    Usage:
    p = PluginHelper()
    p.status(warning)
    p.add_summary('Example Plugin with warning status')
    p.add_metric('cpu load', '90')
    p.exit()
    """
    _nagios_status = -1     # exit status of the plugin
    _long_output = None       # Long output of the plugin
    _summary = None           # Summary of the plugin
    _perfdata = None  # Performance and Threshold Metrics are stored here
    show_longoutput = True  # If True, print longoutput
    show_perfdata = True    # If True, print perfdata
    show_summary = True     # If True, print Summary
    show_status_in_summary = False
    show_legacy = False     # If True, print perfdata in legacy form
    verbose = False         # Extra verbosity
    show_debug = False      # Extra debugging
    timeout = 50            # Default timeout set to little less than nagios service check timeout

    thresholds = None # List of strings in the nagios threshold format
    options = None          # OptionParser() options
    arguments = None        # OptionParser() arguments
    def __init__(self):
        self._long_output = []
        self._summary = []
        self.thresholds = []
        self._perfdata = PerfData()  # Performance and Threshold Metrics are stored here

        self.parser = OptionParser()
        general = OptionGroup(self.parser, "Generic Options")
        self.parser.add_option('--threshold','--th',default=[], help="Thresholds in standard nagios threshold format", metavar='', dest="thresholds",action="append")

        display_group = OptionGroup(self.parser, "Display Options")
        display_group.add_option("-v", "--verbose", dest="verbose", help="Print more verbose info", metavar="v", action="store_true", default=self.verbose)
        general.add_option("-d", "--debug", dest="show_debug", help="Print debug info", metavar="d", action="store_true", default=self.show_debug)
        display_group.add_option("--no-perfdata", dest="show_perfdata", help="Dont show any performance data", action="store_false", default=self.show_perfdata)
        display_group.add_option("--no-longoutput", dest="show_longoutput", help="Hide longoutput from the plugin output (i.e. only display first line of the output)", action="store_false", default=self.show_longoutput)
        display_group.add_option("--no-summary", dest="show_summary", help="Hide summary from plugin output", action="store_false", default=self.show_summary)
        #display_group.add_option("--show-status-in-summary", dest="show_status_in_summary", help="Prefix the summary of the plugin with OK- or WARN- ", action="store_true", default=False)
        display_group.add_option("--get-metrics", dest="get_metrics", help="Print all available metrics and exit (can be combined with --verbose)", action="store_true", default=False)
        display_group.add_option("--legacy", dest="show_legacy", help="Output perfdata in legacy format", action="store_true", default=self.show_legacy)
        self.parser.add_option_group(display_group)

    def parse_arguments(self, argument_list=None):
        """ Parsers commandline arguments, prints error if there is a syntax error.

        Creates:
            self.options   -- As created by OptionParser.parse()
            self.arguments -- As created by OptionParser.parse()
        Arguments:
            argument_list -- By default use sys.argv[1:], override only if you know what you are doing.
        Returns:
            None
        """
        self.options, self.arguments = self.parser.parse_args(args=argument_list)
        # TODO: Handle it if developer decides to remove some options before calling parse_arguments()
        self.thresholds = self.options.thresholds
        self.show_longoutput = self.options.show_longoutput
        self.show_perfdata = self.options.show_perfdata
        self.show_legacy = self.options.show_legacy
        self.show_debug = self.options.show_debug
        self.verbose = self.options.verbose
        #self.show_status_in_summary = self.options.show_status_in_summary

    def add_long_output(self, message):
        """ Appends message to the end of Plugin long_output. Message does not need a \n suffix

        Examples:
          >>> p = PluginHelper()
          >>> p.add_long_output('Status of sensor 1')
          >>> p.add_long_output('* Temperature: OK')
          >>> p.add_long_output('* Humidity: OK')
          >>> p.get_long_output()
          'Status of sensor 1\\n* Temperature: OK\\n* Humidity: OK'
        """
        self._long_output.append(message)

    def get_long_output(self):
        """ Returns all long_output that has been added via add_long_output """
        return '\n'.join(self._long_output)

    def add_summary(self, message):
        """ Adds message to Plugin Summary """
        self._summary.append(message.strip())

    def get_summary(self):
        return '. '.join(self._summary)

    def get_status(self):
        """ Returns the worst nagios status (integer 0,1,2,3) that has been put with add_status()

        If status has never been added, returns 3 for UNKNOWN
        """

        # If no status has been set, return unknown
        if self._nagios_status == -1:
            return UNKNOWN
        else:
            return self._nagios_status

    def status(self, new_status=None):
        """ Same as get_status() if new_status=None, otherwise call add_status(new_status) """
        if new_status is None:
            return self.get_status()
        if new_status not in state_text:
            new_status = unknown
        return self.add_status(new_status)

    def add_status(self, new_status=None):
        """ Update exit status of the nagios plugin. This function will keep history of the worst status added

        Examples:
        >>> p = PluginHelper()
        >>> p.add_status(0) # ok
        >>> p.add_status(2) # critical
        >>> p.add_status(1) # warning
        >>> p.get_status()  #
        2
        """

        # If new status was entered as a human readable string (ok,warn,etc) lets convert it to int:
        if type(new_status) == type(''):
            if new_status.lower() in state:
                new_status = state[new_status]
            else:
                raise Exception("Invalid status supplied \"%s\"" % (new_status))

        self._nagios_status = max(self._nagios_status, new_status)

    def add_metric(self, label="",value="",warn="",crit="",min="",max="",uom="", perfdatastring=None):
        """ Add numerical metric (will be outputted as nagios performanca data)

        Examples:
          >>> p = PluginHelper()
          >>> p.add_metric(label="load1", value="7")
          >>> p.add_metric(label="load5", value="5")
          >>> p.add_metric(label="load15",value="2")
          >>> p.get_perfdata()
          "'load1'=7;;;; 'load5'=5;;;; 'load15'=2;;;;"
        """
        if not perfdatastring is None:
            self._perfdata.add_perfdatametric(perfdatastring=perfdatastring)
        else:
            self._perfdata.add_perfdatametric(label=label,value=value,warn=warn,crit=crit,min=min,max=max,uom=uom)

    def get_metric(self, label):
        """ Return one specific metric (PerfdataMetric object) with the specified label. Returns None if not found. """
        for i in self._perfdata.metrics:
            if i.label == label:
                return i
        return None

    def convert_perfdata(self, perfdata):
        """ Converts new threshold range format to old one. Returns None.

        Examples:
            x..y -> x:y
            inf..y -> :y
            -inf..y -> :y
            x..inf -> x:
            -inf..inf -> :        
        """
        for metric in perfdata:
            metric.warn = metric.warn.replace("..",":").replace("-inf","").replace("inf","")
            metric.crit = metric.crit.replace("..",":").replace("-inf","").replace("inf","")
        return None


    def get_perfdata(self):
        """ Get perfdatastring for all valid perfdatametrics collected via add_perfdata """
        if self.show_legacy == True:
            self.convert_perfdata(self._perfdata.metrics)
        return str(self._perfdata   )

    def get_plugin_output(self, exit_code=None,summary=None, long_output=None, perfdata=None):
        """ Get all plugin output as it would be printed to screen with self.exit() """
        if summary is None:
            summary = self.get_summary()
        if long_output is None:
            long_output = self.get_long_output()
        if perfdata is None:
            perfdata = self.get_perfdata()
        if exit_code is None:
            exit_code = self.get_status()

        return_buffer = ""
        if self.show_status_in_summary == True:
            return_buffer += "%s - " % state_text[exit_code]
        if self.show_summary == True:
            return_buffer += summary
        if self.show_perfdata == True and len(perfdata) > 0:
            return_buffer += " | %s\n" % perfdata

        if not return_buffer.endswith('\n'):
            return_buffer += '\n'
        if self.show_longoutput == True and len(long_output) > 0:
            return_buffer += long_output

        return_buffer = return_buffer.strip()
        return return_buffer

    def exit(self, exit_code=None,summary=None, long_output=None, perfdata=None):
        """ Print all collected output to screen and exit nagios style, no arguments are needed
            except if you want to override default behavior.

        Arguments:
            summary     -- Is this text as the plugin summary instead of self.get_summary()
            long_output -- Use this text as long_output instead of self.get_long_output()
            perfdata    -- Use this text instead of self.get_perfdata()
            exit_code   -- Use this exit code instead of self.status()
        """
        if exit_code is None:
            exit_code = self.get_status()
        if self.options.get_metrics == True:
            summary = "Available metrics for this plugin:"
            metrics = []

            for i in self._perfdata.metrics:
                if self.options.verbose == True:
                    metrics.append( str(i) )
                else:
                    metrics.append( i.label )
            long_output = '\n'.join(metrics)


        plugin_output = self.get_plugin_output(exit_code=exit_code,summary=summary,long_output=long_output,perfdata=perfdata)

        print plugin_output
        sys.exit(exit_code)

    def check_metric(self, metric_name, thresholds):
        """ Check one specific metric against a list of thresholds. Updates self.status() and writes to summary or longout as appropriate.

        Arguments:
          metric_name -- A string representing the name of the metric (the label part of the performance data)
          thresholds  -- a list in the form of [ (level,range) ] where range is a string in the format of "start..end"

        Examples:
        >>> thresholds = [(warning,'2..5'),(critical,'5..inf')]
        >>> p = PluginHelper()
        >>> p.check_metric('load15',thresholds)

        Returns:
          None
        """
        metric = self.get_metric(label=metric_name)

        # If threshold was specified but metric not found in our data, set status unknown
        if metric is None:
            self.status(unknown)
            self.add_summary("Metric %s not found" % (metric_name))
            return

        metric_status = -1 # by default assume nothing
        default_state = 0 # By default if no treshold matches, we assume OK
        highest_level = ok # highest threshold range seen
        # Iterate through all thresholds, and log down warn and crit for perfdata purposes
        for level, threshold_range in thresholds:
            if metric.warn == '' and level == warning:
                metric.warn = threshold_range
            elif metric.crit == '' and level == critical:
                metric.crit = threshold_range
            if level == ok:
                default_state = 2

        # Iterate all threshold and determine states
        for level, threshold_range in thresholds:
            highest_level = max(highest_level, level)
            # If ok threshold was specified, default state is critical according to spec
            # If value matches our threshold, we increment the status
            if new_threshold_syntax.check_range(metric.value, threshold_range):
                metric_status = max(metric_status, level)
                self.debug('%s is within %s range "%s"' % (metric_name, state_text[level], threshold_range))
                if level == ok:
                    self.debug("OK threshold matches, not checking any more thresholds")
                    metric_status = ok
                    break
            else:
                self.debug('%s is outside %s range "%s"' % (metric_name, state_text[level],threshold_range))

        # If no thresholds matched, set a default return code
        if metric_status < 0:
            metric_status = default_state


        # OK's go to long output, errors go directly to summary
        self.add_status(metric_status)
        message = '%s on %s' % (state_text[metric_status], metric_name)

        # Errors are added to the summary:
        if metric_status > 0:
            self.add_summary(message)

        if self.verbose == True:
            self.add_long_output(message)


    def check_all_metrics(self):
        """ Checks all metrics (add_metric() against any thresholds set in self.options.thresholds or with --threshold from commandline)"""
        checked_metrics = []
        for threshold in self.thresholds:
            parsed_threshold = new_threshold_syntax.parse_threshold(threshold)
            metric_name = parsed_threshold['metric']
            thresholds = parsed_threshold['thresholds']
            self.check_metric(metric_name, thresholds)
            checked_metrics.append( metric_name )

        # Lets look at metrics that were not specified on the command-line but might have a default
        # threshold specified with their metric data
        for i in self._perfdata.metrics:
            if i.label in checked_metrics:
                continue
            thresholds = []

            if i.warn != '':
                thresholds.append( (warning, i.warn))
            if i.crit != '':
                thresholds.append( (critical, i.crit))
            self.check_metric(i.label, thresholds)

    def run_function(self, function):
        """ Executes "function" and exits nagios style if there are any exceptions."""
        try:
            function()
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exit_code = unknown
            #traceback.print_exc(file=sys.stdout)
            summary = "Unhandled '%s' exception while running plugin (traceback below)" % exc_type
            long_output = traceback.format_exc()
            self.exit(exit_code=exit_code, summary=summary, long_output=long_output,perfdata='')

    def debug(self, message):
        if self.show_debug == True:
            self.add_long_output("debug: %s" % message)


    def __str__(self):
        return self.get_plugin_output()

    def __repr__(self):
        return self.get_plugin_output(long_output='',perfdata='')
