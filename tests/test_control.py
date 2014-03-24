import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
from mock import MagicMock, patch, Mock

import pynag.Control
from pynag.Parsers import config

class testControl(unittest.TestCase):
    def setUp(self):
        """
        Set to the current defaults of the control.daemon() class
        It's probably dangerous to read these variables from the class object itself
        """
        self.config = config()

        self.nagios_bin=self.config.guess_nagios_binary()
        self.nagios_cfg='/etc/nagios/nagios.cfg'
        self.nagios_init = '/etc/init.d/nagios'

        self.control = pynag.Control.daemon(
                nagios_bin=self.nagios_bin,
                nagios_cfg=self.nagios_cfg,
                nagios_init=self.nagios_init)

    def fake_popen(self, stdout=None, stderr=None, return_value=0):
        # Patch popen
        self.popen_patcher = patch('pynag.Control.Popen')
        self.mock_popen = self.popen_patcher.start()

        # Set defaults for popen patching
        self.mock_rv = Mock()
        self.mock_rv.communicate.return_value = [stdout, stderr]
        self.mock_rv.wait.return_value = return_value

        self.mock_popen.return_value = self.mock_rv

    def fake_popen_stop(self):
        self.popen_patcher.stop()

    def test_verify_config_success(self):
        # Patch all calls to Popen
        self.fake_popen()

        # Run the actual daemon.verify_config
        result = self.control.verify_config()

        # Should verify correctly
        self.assertTrue(result)

        # Make sure popen is called correctly
        self.mock_popen.assert_called_once_with([self.nagios_bin, "-v", self.nagios_cfg],
            shell=False,
            stdout=pynag.Control.PIPE,
            stderr=pynag.Control.PIPE
            )

        # End patching of Popen
        self.fake_popen_stop()

    def test_verify_config_failure(self):
        # Patch all calls to Popen, make calls return exit code 1
        self.fake_popen(return_value=1)

        # Run the actual daemon.verify_config
        result = self.control.verify_config()

        # Should return None on verify error
        self.assertEqual(result, None)

        # Make sure popen is called correctly
        self.mock_popen.assert_called_once_with([self.nagios_bin, "-v", self.nagios_cfg],
            shell=False,
            stdout=pynag.Control.PIPE,
            stderr=pynag.Control.PIPE
            )

        # End patching of Popen
        self.fake_popen_stop()

    def test_restart(self):
        os.system = MagicMock()
        os.system.return_value = 0

        self.control.restart()

        os.system.assert_called_once_with("%s restart" % self.nagios_init)

    def test_status(self):
        os.system = MagicMock()
        os.system.return_value = 0

        self.control.status()

        os.system.assert_called_once_with("%s status" % self.nagios_init)

    def test_reload(self):
        os.system = MagicMock()
        os.system.return_value = 0

        self.control.reload()

        os.system.assert_called_once_with("%s reload" % self.nagios_init)


if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
