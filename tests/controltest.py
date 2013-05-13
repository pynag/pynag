import unittest
from mock import MagicMock

import os
from pynag.Control import daemon

class testControl(unittest.TestCase):
    def setUp(self):
        self.nagios_bin = '/usr/bin/nagios'
        self.nagios_cfg = '/etc/nagios/nagios.cfg'
        self.nagios_init = '/etc/init.d/nagios'

    def test_verify_config_success(self):
        control = daemon(nagios_bin = self.nagios_bin,
            nagios_cfg = self.nagios_cfg, nagios_init = self.nagios_init)
        os.system = MagicMock()
        os.system.return_value = 0
        
        result = control.verify_config()
        self.assertTrue(result)
        os.system.assert_called_once_with("%s -v %s" % (self.nagios_bin, self.nagios_cfg))

    def test_verify_config_failure(self):
        control = daemon(nagios_bin = self.nagios_bin,
            nagios_cfg = self.nagios_cfg, nagios_init = self.nagios_init)
        os.system = MagicMock()
        os.system.return_value = 1
        
        result = control.verify_config()
        self.assertEqual(result, None)
        os.system.assert_called_once_with("%s -v %s" % (self.nagios_bin, self.nagios_cfg))

    def test_restart(self):
        control = daemon(nagios_bin = self.nagios_bin,
            nagios_cfg = self.nagios_cfg, nagios_init = self.nagios_init)
        os.system = MagicMock()
        os.system.return_value = 0

        control.restart()

        os.system.assert_called_once_with("%s restart" % self.nagios_init)

    def test_status(self):
        control = daemon(nagios_bin = self.nagios_bin,
            nagios_cfg = self.nagios_cfg, nagios_init = self.nagios_init)
        os.system = MagicMock()
        os.system.return_value = 0

        control.status()

        os.system.assert_called_once_with("%s status" % self.nagios_init)

    def test_reload(self):
        control = daemon(nagios_bin = self.nagios_bin,
            nagios_cfg = self.nagios_cfg, nagios_init = self.nagios_init)
        os.system = MagicMock()
        os.system.return_value = 0

        control.reload()

        os.system.assert_called_once_with("%s reload" % self.nagios_init)
