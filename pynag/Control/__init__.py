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

import sys
import os
import re


class daemon:
	"""
	Control the nagios daemon through python
	"""

	def __init__(self, nagios_bin = "/usr/bin/nagios", nagios_cfg = "/etc/nagios/nagios.cfg", nagios_init = "/etc/init.d/nagios"):

		if not os.path.isfile(nagios_bin):
			sys.stderr.write("Missing Nagios Binary (%s)\n" % nagios_bin)
			return

		if not os.path.isfile(nagios_cfg):
			sys.stderr.write("Missing Nagios Configuration (%s)\n" % nagios_cfg)
			return

		if not os.path.isfile(nagios_init):
			sys.stderr.write("Missing Nagios Init File (%s)\n" % nagios_init)
			return

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
