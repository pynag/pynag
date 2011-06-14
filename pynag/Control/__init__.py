# -*- coding: utf-8 -*-

import sys
import os
import re

"""
Python Nagios extensions
"""

class daemon:
	"""
	Control the nagios daemon through python
	"""

	def __init__(self, nagios_bin = "/usr/bin/nagios", nagios_cfg = "/etc/nagios/nagios.cfg", nagios_init = "/etc/init.d/nagios"):

		if not os.path.isfile(nagios_bin):
			sys.stderr.write("Missing Nagios Binary (%s)\n" % nagios_bin)
			return None

		if not os.path.isfile(nagios_cfg):
			sys.stderr.write("Missing Nagios Configuration (%s)\n" % nagios_cfg)
			return None

		if not os.path.isfile(nagios_init):
			sys.stderr.write("Missing Nagios Init File (%s)\n" % nagios_init)
			return None

		self.nagios_bin = nagios_bin
		self.nagios_cfg = nagios_cfg
		self.nagios_init = nagios_init

	def verify_config(self):
		"""
		Run nagios -v config_file to verify that the conf is working
		"""

		cmd = "%s -v %s" % (self.nagios_bin, self.nagios_cfg)

		result = os.system(cmd)

		if result == 0:
			return True
		else:
			return None

	def restart(self):
		cmd = "%s restart" % self.nagios_init

		os.system(cmd)
	def reload(self):
		cmd = "%s reload" % self.nagios_init

		os.system(cmd)