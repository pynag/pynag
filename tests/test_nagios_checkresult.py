#! /usr/bin/python

import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tempfile import mkdtemp
from pynag.Utils import CheckResult

class TestNagiosCheckResult(unittest.TestCase):
    def _findstr(self, file_name, string):
        """Returns true if string found in file"""
        fh = open(file_name)
        output = fh.read()
        fh.close()
        return string in output

    def setUp (self):
        self.tempdir = mkdtemp()
        self.check_result = CheckResult(self.tempdir)

    def test_header(self):
        """Test if the result header is correct"""
        filename = self.check_result.submit()

        self.assertTrue(self._findstr(
            filename,
            "### Active Check Result File ###\n"
        ))

        self.assertTrue(self._findstr(
            filename,
            "file_time=%s\n" % self.check_result.file_time
        ))

    def test_service(self):
        """Test if the service is created correctly"""
        self.check_result.service_result('testhost', 'test service')
        filename = self.check_result.submit()

        self.assertTrue(self._findstr(
            filename,
            '\nhost_name=testhost\n'
        ))
        self.assertTrue(self._findstr(
            filename,
            '\nservice_description=test service\n'
        ))

    def test_host(self):
        """Test if the host is created correctly"""
        self.check_result.host_result('testhost')
        filename = self.check_result.submit()

        self.assertTrue(self._findstr(
            filename,
            '\nhost_name=testhost\n'
        ))

def __findstr(self, file, string):
    """Returns true if string found in file"""
    fh = open(file)
    output = fh.read()
    fh.close()
    return string in output

if __name__ == '__main__':
    unittest.main()
