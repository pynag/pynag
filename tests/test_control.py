#!/usr/bin/env python

import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
from mock import MagicMock, patch, Mock

import pynag.Control
from pynag.Parsers import config

import warnings

class testControl(unittest.TestCase):
    def setUp(self):
        """
        Set to the current defaults of the control.daemon() class
        It's probably dangerous to read these variables from the class object itself
        """
        self.config = config()

        # Ignore futurewarnings for nagios_init
        warnings.simplefilter("ignore", FutureWarning)

        self.nagios_bin=self.config.guess_nagios_binary()
        self.nagios_cfg='/etc/nagios/nagios.cfg'
        self.service_name = 'nagios'
        self.nagios_init = "service nagios"

        self.control = pynag.Control.daemon(
                nagios_bin=self.nagios_bin,
                nagios_cfg=self.nagios_cfg,
                nagios_init=self.nagios_init,
                service_name=self.service_name)

    def test_verify_config_success(self):
        # Patch all calls to Popen
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        # Run the actual daemon.verify_config
        result = self.control.verify_config()

        # Should verify correctly
        self.assertTrue(result)

        # Make sure runCommand is called correctly
        pynag.Control.runCommand.assert_called_once_with(["sudo", self.nagios_bin, "-v", self.nagios_cfg],
            shell=False
            )

    def test_verify_config_failure(self):
        # Patch all calls to Popen, make calls return exit code 1
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [2, "", "Permission denied"]

        # Run the actual daemon.verify_config
        result = self.control.verify_config()

        # Should return None on verify error
        self.assertEqual(result, None)

        # Make sure runCommand is called correctly
        pynag.Control.runCommand.assert_called_once()
        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_bin, "-v", self.nagios_cfg],
            shell=False)

    def test_restart_script(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Restarted", ""]

        self.control.method = self.control.SYSV_INIT_SCRIPT
        result = self.control.restart()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_init, "restart"], shell=False)

    def test_restart_service(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Restarted", ""]

        self.control.method = self.control.SYSV_INIT_SERVICE
        result = self.control.restart()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "restart"], shell=False)

    def test_restart_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        result = self.control.restart()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "restart"], shell=False)

    def test_status_script(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Running just fine", ""]

        self.control.method = self.control.SYSV_INIT_SCRIPT
        result = self.control.status()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_init, "status"], shell=False)

    def test_status_service(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Running just fine", ""]

        self.control.method = self.control.SYSV_INIT_SERVICE
        result = self.control.status()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "status"], shell=False)

    def test_status_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        result = self.control.status()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "status"], shell=False)

    def test_reload_script(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Reloaded just fine", ""]

        self.control.method = self.control.SYSV_INIT_SCRIPT
        self.control.reload()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_init, "reload"], shell=False)

    def test_reload_service(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Reloaded just fine", ""]

        self.control.method = self.control.SYSV_INIT_SERVICE
        self.control.reload()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "reload"], shell=False)

    def test_reload_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        self.control.reload()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "reload"], shell=False)

    def test_stop_script(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Stopped service", ""]

        self.control.method = self.control.SYSV_INIT_SCRIPT
        self.control.stop()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_init, "stop"], shell=False)

    def test_stop_service(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Stopped service", ""]

        self.control.method = self.control.SYSV_INIT_SERVICE
        self.control.stop()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "stop"], shell=False)

    def test_stop_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        self.control.stop()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "stop"], shell=False)

    def test_start_script(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Started service", ""]

        self.control.method = self.control.SYSV_INIT_SCRIPT
        self.control.start()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", self.nagios_init, "start"], shell=False)

    def test_start_service(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "OK Started service", ""]

        self.control.method = self.control.SYSV_INIT_SERVICE
        self.control.start()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "start"], shell=False)

    def test_start_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        self.control.start()

        pynag.Control.runCommand.assert_called_once_with(
            ["sudo", "service", self.service_name, "start"], shell=False)

    def test_running_script(self):
        pynag.Parsers.config._get_pid = MagicMock()
        pynag.Parsers.config._get_pid.return_value = 1024

        self.control.method = self.control.SYSV_INIT_SCRIPT
        running = self.control.running()

        self.assertEqual(running, True)
        pynag.Parsers.config._get_pid.assert_called_once_with()

    def test_running_service(self):
        pynag.Parsers.config._get_pid = MagicMock()
        pynag.Parsers.config._get_pid.return_value = 1024

        self.control.method = self.control.SYSV_INIT_SERVICE
        running = self.control.running()

        self.assertEqual(running, True)
        pynag.Parsers.config._get_pid.assert_called_once_with()

    def test_running_systemd(self):
        pynag.Control.runCommand = MagicMock()
        pynag.Control.runCommand.return_value = [0, "", ""]

        self.control.method = self.control.SYSTEMD
        running = self.control.running()

        self.assertEqual(running, True)
        pynag.Control.runCommand.assert_called_once_with(
            ["systemctl", "is-active", self.service_name], shell=False)

    def test_running_failed_script(self):
        pynag.Parsers.config._get_pid = MagicMock()
        pynag.Parsers.config._get_pid.return_value = None

        self.control.method = self.control.SYSV_INIT_SCRIPT
        running = self.control.running()

        self.assertEqual(running, False)
        pynag.Parsers.config._get_pid.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
