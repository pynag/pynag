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
import re
from platform import node
from optparse import OptionParser
from popen2 import Popen3


# Map the return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

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
            self.data['verbosity'] = options.verbose
        else:
            self.data['verbosity'] = 0

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

        ## Set Critical
        if options.critical:
            self.data['critical'] = options.critical
        else: self.data['critical'] = None

        ## Set Warn
        if options.warning:
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
        critical = self.data['critical']
        warning = self.data['warning']
        self.hr_range = ""

        if critical and self._range_checker(value, critical):
            self.add_message(CRITICAL,"%s is within critical range: %s" % (value, critical))
        elif warning and self._range_checker(value, warning):
            self.add_message(WARNING,"%s is within warning range: %s" % (value, warning))
        else:
            self.add_message(OK,"%s is outside warning=%s and critical=%s" % (value, warning, critical))

        # Get all messages appended and exit code
        (code, message) = self.check_messages()

        # Exit with appropriate exit status and message
        self.nagios_exit(code, message)

    def _range_checker(self, value, range_threshold):
        """ deprecated. Use pynag.Plugins.check_range() """
        return check_range(value=value, range_threshold=range_threshold)

    def send_nsca(self, code, message, ncsahost, hostname=node(), service=None):
        """
        Send data via send_nsca for passive service checks
        """
    
        # Execute send_nsca
        command = "send_nsca -H %s" % ncsahost
        p = Popen3(command,  capturestderr=True)

        # Service check
        if service:
            print >>p.tochild, "%s    %s    %s    %s %s" % (hostname, service, code, message, self.perfdata_string())
        # Host check, omit service_description
        else:
            print >>p.tochild, "%s    %s    %s %s" % (hostname, code, message, self.perfdata_string())

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
    >>> check_threshold(88, warning="90:", critical="95:")
    0
    >>> check_threshold(92, warning="90:", critical="95:")
    1
    >>> check_threshold(96, warning="90:", critical="95:")
    2
    """
    if critical and check_range(value, critical):
        return CRITICAL
    elif warning and check_range(value, warning):
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
        True  -- If value is inside the range (alert if this happens)
        False -- If value is outside the range

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


    # Example runs for doctest, True should mean alert
    >>> check_range(78, "90:") # Example disk is 78% full, threshold is 90
    False
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
    """

    # if no range_threshold is provided, assume everything is ok
    if not range_threshold:
        range_threshold='~:'
    range_threshold = str(range_threshold)
    # If range starts with @, then we do the opposite
    if range_threshold[0] == '@':
        return not check_range(value, range_threshold[1:])

    value = float(value)
    if range_threshold.find(':') > -1:
        (start,end) = (range_threshold.split(':', 1))
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
    if start is not None and float(value) < float(start):
        return False
    if end is not None and float(value) > float(end):
        return False
    return True
