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
The Control module includes classes to control the Nagios service
and the Command submodule wraps Nagios commands.
"""

import sys
import os
import re

from pynag.Utils import PynagError

class daemon:
    """
    Control the nagios daemon through python
    """

    def __init__(self, nagios_bin = "/usr/bin/nagios", nagios_cfg = "/etc/nagios/nagios.cfg", nagios_init = "/etc/init.d/nagios"):

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
        """
        Restarts Nagios via it's init script.
        """
        cmd = "%s restart" % self.nagios_init

        return os.WEXITSTATUS(os.system(cmd))
    def status(self):
        """
        Returns the status of the Nagios service.
        """
        cmd = "%s status" % self.nagios_init

        return os.WEXITSTATUS(os.system(cmd))
    def reload(self):
        """
        Reloads Nagios via it's init script.
        """
        cmd = "%s reload" % self.nagios_init

        return os.WEXITSTATUS(os.system(cmd))
