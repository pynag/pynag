from __future__ import absolute_import
import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
import tempfile
import shutil

from tests import tests_dir

os.chdir(tests_dir)
import pynag.Model

# Exported to pynag command
pynagbase = os.path.realpath("%s/%s" % (tests_dir, os.path.pardir))


class testDatasetParsing(unittest.TestCase):

    """ Parse any dataset in the tests directory starting with "testdata" """

    def setUp(self):
        """ Basic setup before test suite starts
        """
        os.chdir(tests_dir)
        self.tmp_dir = tempfile.mkdtemp()  # Will be deleted after test runs
        # os.mkdir(self.tmp_dir)
        pynag.Model.pynag_directory = self.tmp_dir

    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def testParseDatasets(self):
        """ Parse every testdata*/nagios/nagios.cfg
        Output will be compared with testdata*/expectedoutput.txt
        """
        test_dirs = []
        for i in os.listdir('.'):
            if i.startswith('testdata') and os.path.isdir(i) and os.path.isfile(i + "/nagios/nagios.cfg"):
                test_dirs.append(i)

        for directory in test_dirs:
            os.chdir(directory)
            pynag.Model.cfg_file = "./nagios/nagios.cfg"
            pynag.Model.config = None
            actualOutput = ''
            for i in pynag.Model.ObjectDefinition.objects.all:
                actualOutput += str(i)
                # Write our parsed data to tmpfile so we have an easy diff later:
            tmp_file = self.tmp_dir + "/" + os.path.basename(directory) + "_actual_output.txt"
            open(tmp_file, 'w').write(actualOutput)
            diff_output = pynag.Utils.runCommand("diff -uwB expected_output.txt '%s'" % tmp_file)[1]
            self.assertEqual('', diff_output)


class testsFromCommandLine(unittest.TestCase):

    """ Various commandline scripts
    """

    def setUp(self):
        # Import pynag.Model so that at the end we can see if configuration changed at all
        pynag.Model.ObjectDefinition.objects.get_all()

    def tearDown(self):
        # Check if any configuration changed while we were running tests:
        self.assertEqual(False, pynag.Model.config.needs_reparse(), "Seems like nagios configuration changed while running the unittests. Some of the tests might have made changes!")

    def testCommandPluginTest(self):
        """ Run Tommi's plugintest script to test pynag plugin threshold parameters
        """
        expected_output = (0, '', '')  # Expect exit code 0 and no output
        actual_output = pynag.Utils.runCommand(pynagbase + '/scripts/plugintest')
        self.assertEqual(expected_output, actual_output)

    def testCommandPynag(self):
        """ Various command line tests on the pynag command  """
        pynag_script = pynagbase + '/scripts/pynag'
        # ok commands, bunch of commandline commands that we execute just to see
        # if an unhandled exception appears,
        # Ideally none of these commands should modify any configuration
        ok_commands = [
            "%s list" % pynag_script,
            "%s list where host_name=localhost and object_type=host" % pynag_script,
            "%s list where host_name=localhost and object_type=host --json --debug" % pynag_script,
            "%s update where nonexistantfield=test set nonexistentfield=pynag_unit_testing" % pynag_script,
            "%s config --get cfg_dir" % pynag_script,
        ]
        for i in ok_commands:
            exit_code, stdout, stderr = pynag.Utils.runCommand(i,
                                                               env={'PYTHONPATH': pynagbase})
            self.assertEqual(0, exit_code, "Error when running command %s\nexit_code: %s\noutput: %s\nstderr: %s" % (i, exit_code, stdout, stderr))

if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
