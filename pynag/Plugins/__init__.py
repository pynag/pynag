#!/usr/bin/python
import sys
import os
import re
from optparse import OptionParser

"""
Python Nagios extensions
"""

__author__ = "Drew Stinnett"
__copyright__ = "Copyright 2008, Drew Stinnett"
__credits__ = ["Drew Stinnett"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Drew Stinnett"
__email__ = "drew@drewlink.com"
__status__ = "Development"

class simple:
	"""
	Nagios plugin helper library based on Nagios::Plugin
	"""

	def __init__(self, shortname = None, version = None, blurb = None, extra = None, url = None, license = None, plugin = None, timeout = 15 ):

		## this is the custom parser
		self.extra_list_optional = []
		self.extra_list_required = []

		## Set the option parser stuff here
		self.parser = OptionParser()

		## Variables we'll get later
		self.opts = None
		self.data = {}
		self.data['perfdata'] = None
		self.data['threshhold'] = None

		## Error mappings, for easy access
		self.errors = { "OK":0, "WARNING":1, "CRITICAL":2, "UNKNOWN":3, }
		self.status_text = { 0:"OK", 1:"WARNING", 2:"CRITICAL", 3:"UNKNOWN", }

		## Shortname creation
		if not shortname:
			self.data['shortname'] = os.path.basename("%s" % sys.argv[0])
		else:
			self.data['shortname'] = shortname

		## Status messages
		self.data['messages'] = { "warning":None, "critical":None, "ok":None }

	def add_arg(self, spec_abbr, spec, help_text, required=1):
		"""
		Add an argument to be handled by the option parser.  By default, the arg is not required
		"""
		self.parser.add_option("-%s" % spec_abbr, "--%s" % spec, dest="%s" % spec, help=help_text, metavar="%s" % spec.upper())
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

		if not options.critical and not options.warning:
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

	def add_perfdata(self, label , value , uom = None, threshold = None):
		"""
		Append perfdata string to the end of the message
		"""
		## Create this, if it doesn't already exist
		if not self.data['perfdata']:
			self.data['perfdata'] = "|"

		self.data['perfdata'] += "%s=%s" % (label, value)

	def check_range(self, value):
		"""
		Check if a value is within a given range.  This should replace change_threshold eventually

		Taken from:  http://nagiosplug.sourceforge.net/developer-guidelines.html
		Range definition
	
		Generate an alert if x...
		10		< 0 or > 10, (outside the range of {0 .. 10})
		10:		< 10, (outside {10 .. #})
		~:10	> 10, (outside the range of {-# .. 10})
		10:20	< 10 or > 20, (outside the range of {10 .. 20})
		@10:20	# 10 and # 20, (inside the range of {10 .. 20})
		"""
		critical = self.data['critical']
		warning = self.data['warning']

		if critical and self._range_checker(value, critical):
			self.nagios_exit("CRITICAL","%s meets the range: %s" % (value, critical))

		if warning and self._range_checker(value, warning):
			self.nagios_exit("WARNING","%s meets the range: %s" % (value, warning))

		## This is the lowest range, which we'll output
		if warning:
			alert_range = warning
		else:
			alert_range = critical
		
		self.nagios_exit("OK","%s does not meet the range: %s" % (value, alert_range))

	def _range_checker(self, value, check_range):
		"""
		Builtin check using nagios development guidelines
		"""
		import re

		## Simple number check
		simple_num_re = re.compile('^\d+$')
		if simple_num_re.match(str(check_range)):
			value = float(value)
			check_range = float(check_range)
			if value < 0:
				return True
			elif value > check_range:
				return True
			else:
				return False

		if (check_range.find(":") != -1) and (check_range.find("@") == -1):
			(start, end) = check_range.split(":")
			if (end == "") and (float(value) < float(start)):
				return True
			elif (start == "~") and (float(value) > float(end)):
				return True
			else:
				return False

		## Inclusive range check
		if check_range[0] == "@":
			(start, end) = check_range[1:].split(":")
			start = float(start)
			end = float(end)
			if ( float(value) >= start ) and ( float(value) <= end ):
				return True
			else:
				return False

	def nagios_exit(self, code_text, message):
		"""
		Exit with exit_code, message, and optionally perfdata
		"""
		## Append perfdata to the message, if perfdata exists
		if self.data['perfdata']:
			append = self.data['perfdata']
		else:
			append = ""

		## This should be one line (or more in nagios 3)
		print "%s : %s %s" % (code_text, message, append)
		sys.exit(self.errors[code_text])

	def __setitem__(self, key, item):
		self.data[key] = item

	def __getitem__(self, key):
		return self.data[key]
