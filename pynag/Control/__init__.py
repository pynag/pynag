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

import os
import pynag.Utils
from warnings import warn

from pynag.Utils import PynagError, runCommand

class daemon(object):
    """
    Control the nagios daemon through python

    >>> from pynag.Control import daemon
    >>>
    >>> d = daemon()   # doctest: +SKIP
    >>> d.restart()    # doctest: +SKIP
    """

    SYSV_INIT_SCRIPT = 1
    SYSV_INIT_SERVICE = 2
    SYSTEMD = 3

    systemd_service_path = "/usr/lib/systemd/system"

    def __init__(self,
                 nagios_bin="/usr/bin/nagios",
                 nagios_cfg="/etc/nagios/nagios.cfg",
                 nagios_init=None,
                 sudo=True,
                 shell=None,
                 service_name="nagios",
                 nagios_config=None
                 ):
        self.nagios_bin = nagios_bin
        self.nagios_cfg = nagios_cfg
        self.nagios_init = nagios_init
        self.service_name = service_name
        self.sudo = sudo
        self.stdout = ""
        self.stderr = ""
        self.nagios_config = nagios_config

        self._deprecate_sudo()
        self.method = self._guess_method()

        if shell:
            warn("shell is deprecated and not necessary anymore",
                 FutureWarning)
        if nagios_init:
            warn("nagios_init is deprecated, use service_name instead",
                 FutureWarning)

    def verify_config(self):
        """
        Run nagios -v config_file to verify that the conf is working

        :returns:   True -- if pynag.Utils.runCommand() returns 0, else None
        """
        cmd = [self.nagios_bin, "-v", self.nagios_cfg]
        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        if result == 0:
            return True
        else:
            return None

    def running(self):
        """
        Checks if the daemon is running

        :returns: Whether or not the daemon is running
        :rtype: bool
        """
        if self.method == daemon.SYSV_INIT_SCRIPT or \
           self.method == daemon.SYSV_INIT_SERVICE:
            if self.nagios_config == None:
                self.nagios_config = pynag.Parsers.config()
            if self.nagios_config._get_pid():
                return True
        elif self.method == daemon.SYSTEMD:
            result = runCommand(["systemctl",
                                 "is-active",
                                 self.service_name], shell=False)
            if result[0] == 0:
                return True
        return False

    def restart(self):
        """
        Restarts Nagios via it's init script.

        :returns: Return code of the restart command ran by pynag.Utils.runCommand()
        :rtype: int
        """
        if self.method == daemon.SYSV_INIT_SCRIPT:
            cmd = [self.nagios_init, "restart"]
        else:
            cmd = ["service", self.service_name, "restart"]

        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        return result

    def status(self):
        """
        Obtain the status of the Nagios service.

        :returns: Return code of the status command ran by pynag.Utils.runCommand()
        :rtype: int
        """
        if self.method == daemon.SYSV_INIT_SCRIPT:
            cmd = [self.nagios_init, "status"]
        else:
            cmd = ["service", self.service_name, "status"]

        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        return result

    def start(self):
        """
        Start the Nagios service.

        :returns: Return code of the start command ran by pynag.Utils.runCommand()
        :rtype: int
        """
        if self.method == daemon.SYSV_INIT_SCRIPT:
            cmd = [self.nagios_init, "start"]
        else:
            cmd = ["service", self.service_name, "start"]

        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        return result

    def stop(self):
        """
        Stop the Nagios service.

        :returns: Return code of the stop command ran by pynag.Utils.runCommand()
        :rtype: int
        """
        if self.method == daemon.SYSV_INIT_SCRIPT:
            cmd = [self.nagios_init, "stop"]
        else:
            cmd = ["service", self.service_name, "stop"]

        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        return result

    def reload(self):
        """
        Reloads Nagios.

        :returns: Return code of the reload command ran by pynag.Utils.runCommand()
        :rtype: int
        """
        if self.method == daemon.SYSV_INIT_SCRIPT:
            cmd = [self.nagios_init, "reload"]
        else:
            cmd = ["service", self.service_name, "reload"]

        if self.sudo:
            cmd.insert(0, 'sudo')

        result, self.stdout, self.stderr = runCommand(cmd, shell=False)

        return result

    def _guess_method(self):
        """
        Guesses whether to run via SYSV INIT script og via systemd.

        Will also modify nagios_init="service nagios" and set
        service_name=nagios and method to SYSV_INIT_SCRIPT

        :returns: ``deamon.SYSTEMD``
        :rtype: int
        """
        if self.nagios_init and os.path.exists(self.nagios_init):
            return daemon.SYSV_INIT_SCRIPT
        elif self.nagios_init and \
             self.nagios_init.split(None, 1)[0].endswith("service"):
            self.service_name = self.nagios_init.split(None, 1)[1]
            return daemon.SYSV_INIT_SERVICE
        elif os.path.exists("%s/%s.service" % (daemon.systemd_service_path,
                                               self.service_name)):
            return daemon.SYSTEMD
        else:
            raise PynagError("Unable to detect daemon method, " \
                            "could not find init script or " \
                            "systemd unit file")

    def _deprecate_sudo(self):
        """
        Warns with a FutureWarning if sudo is being used in nagios_init or
        nagios_bin. It will also remove sudo from the command line and set
        sudo to True
        """
        if self.nagios_init and \
           self.nagios_init.split(None, 1)[0].endswith("sudo"):
            self.sudo = True
            self.nagios_init = self.nagios_init.split(None, 1)[1]
            warn("nagios_init command line with sudo is deprecated, please "
                 "use sudo=True for daemon()", FutureWarning)

        if self.nagios_bin and \
           str(self.nagios_bin.split(None, 1)[0]).endswith("sudo"):
            self.sudo = True
            self.nagios_bin = self.nagios_bin.split(None, 1)[1]
            warn("nagios_bin command line with sudo is deprecated, please "
                 "use sudo=True for daemon()", FutureWarning)


