#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2011 Pall Sigurdsson
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

import unittest
import doctest
import tempfile
import shutil
import os
import sys

tests_dir = os.path.dirname( os.path.realpath(__file__) )
if tests_dir == '':
    tests_dir = '.'
pynagbase = os.path.realpath("%s/%s" % (tests_dir, os.path.pardir))

# sys.path[0] Must be set before importing any pynag modules
sys.path[0] = pynagbase

import pynag.Model
import pynag.Parsers
import pynag.Utils
import pynag.Plugins

# Must run within test dir for relative paths to tests
os.chdir(tests_dir)

class testParsers(unittest.TestCase):
    """ Basic unit tests of Parsers module
    """
    def testLivestatus(self):
        "Test mk_livestatus integration"
	try:
            livestatus = pynag.Parsers.mk_livestatus()
	# Throws parser error if livestatus not running
	except pynag.Parsers.ParserError:
	    self.skipTest("Parsererror, livestatus probably not running")
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")
    def testConfig(self):
        "Test pynag.Parsers.config()"
        c = pynag.Parsers.config()
        c.parse()
        self.assertGreater(len(c.data), 0, "pynag.Parsers.config.parse() ran and afterwards we see no objects. Empty configuration?")
    def testStatus(self):
        "Unit test for pynag.Parsers.status()"
        s = pynag.Parsers.status()
        try:
            s.parse()
        except IOError:
            self.skipTest("IOError, probably no nagios running")
        # Get info part from status.dat file
        info = s.data['info']

        # It only has one object so..
        info = info[0]

        # Try to get current version of nagios
        version = info['version']
    def testObjectCache(self):
        "Test pynag.Parsers.object_cache"
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertGreater(len(o.data.keys()), 0, 'Object cache seems to be empty')

class testModel(unittest.TestCase):
    """
    Basic Unit Tests that relate to saving objects
    """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        self.tmp_dir = tempfile.mkdtemp() # Will be deleted after test runs
        #os.mkdir(self.tmp_dir)
        pynag.Model.pynag_directory = self.tmp_dir
    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir,ignore_errors=True)
    def testSuggestedFileName(self):
        """ Test get_suggested_filename feature in pynag.Model
        """
        s1 = pynag.Model.Service()
        s1.service_description = 'Service without host_name'

        s2 = pynag.Model.Service()
        s2.service_description = 'Service with host_name'
        s2.host_name = 'host.example.com'

        s3 = pynag.Model.Service()
        s3.service_description = 'Service with Generic Name'
        s3.name = 'generic-test-service'

        s1_expected = '%s/services/Service without host_name.cfg' % pynag.Model.pynag_directory
        s2_expected = '%s/services/host.example.com/Service with host_name.cfg' % pynag.Model.pynag_directory
        s3_expected = '%s/services/generic-test-service.cfg' % pynag.Model.pynag_directory

        self.assertEqual(s1_expected, s1.get_suggested_filename() )
        self.assertEqual(s2_expected, s2.get_suggested_filename() )
        self.assertEqual(s3_expected, s3.get_suggested_filename() )

    def testParseDatasets(self):
        """ Parse every testdata*/nagios/nagios.cfg
        Output will be compared with testdata*/expectedoutput.txt
        """
        test_dirs = []
        for i in os.listdir('.'):
            if i.startswith('testdata') and os.path.isdir(i) and os.path.isfile(i + "/nagios/nagios.cfg"):
                test_dirs.append(i)

        for dir in test_dirs:
            os.chdir(dir)
            pynag.Model.cfg_file = "./nagios/nagios.cfg"
            pynag.Model.config = None
            actualOutput = ''
            expectedOutput = open("expected_output.txt").read()
            for i in pynag.Model.ObjectDefinition.objects.all:
                actualOutput += str(i)
            # Write our parsed data to tmpfile so we have an easy diff later:
            tmp_file = self.tmp_dir + "/" + os.path.basename(dir) + "_actual_output.txt"
            open(tmp_file,'w').write(actualOutput)
            diff_output = pynag.Utils.runCommand("diff -uwB expected_output.txt '%s'" % (tmp_file))[1]
            print diff_output
            self.assertEqual('', diff_output)
    def testChangeAttribute(self):
        """ Change a single attribute in a pynag Model object
        """

        s = pynag.Model.Service()
        service_description = "Test Service Description"
        host_name = "testhost.example.com"
        macro = "This is a test macro"
        check_command = "my_check_command"

        # Assign the regular way
        s.service_description = service_description

        # Assign with set_attribute
        s.set_attribute('check_command',check_command)

        # Assign hashmap style
        s['host_name'] = host_name

        # Assign a macro
        s['__TEST_MACRO'] = macro

        self.assertEqual(service_description, s['service_description'])
        self.assertEqual(host_name, s.host_name)
        self.assertEqual(macro, s['__TEST_MACRO'])
        self.assertEqual(check_command, s.get_attribute('check_command'))

class testsFromCommandLine(unittest.TestCase):
    """ Various commandline scripts
    """
    def setUp(self):
        # Import pynag.Model so that at the end we can see if configuration changed at all
        s = pynag.Model.ObjectDefinition.objects.all
    def tearDown(self):
        # Check if any configuration changed while we were running tests:
        self.assertEqual(False, pynag.Model.config.needs_reparse(), "Seems like nagios configuration changed while running the unittests. Some of the tests might have made changes!")
    def testCommandPluginTest(self):
        """ Run Tommi's plugintest script to test pynag plugin threshold parameters
        """
        expected_output = (0,'','') # Expect exit code 0 and no output
        actual_output = pynag.Utils.runCommand(pynagbase + '/scripts/plugintest')
        self.assertEqual(expected_output,actual_output)
    def testCommandPynag(self):
        """ Various command line tests on the pynag command  """
        pynag_script = pynagbase + '/scripts/pynag'
        # ok commands, bunch of commandline commands that we execute just to see
        # if an unhandled exception appears,
        # Ideally none of these commands should modify any configuration
        ok_commands = [
            "%s list" % pynag_script,
            "%s list where host_name=localhost and object_type=host" % pynag_script,
            "%s update where nonexistantfield=test set nonexistentfield=pynag_unit_testing" % pynag_script,
            "%s config --get cfg_dir" % pynag_script,
        ]
        for i in ok_commands:
            exit_code,stdout,stderr = pynag.Utils.runCommand(i)
            self.assertEqual(0, exit_code, "Error when running command %s\nexit_code: %s\noutput: %s\nstderr: %s" % (i,exit_code,stdout,stderr))


def suite():
    suite = unittest.TestSuite()

    # Include tests of Model
    suite.addTest(unittest.makeSuite(testModel))

    # Include tests of Parsers
    suite.addTest(unittest.makeSuite(testParsers))

    # Include commandline tests like the one in ../scripts/plugintest
    suite.addTest(unittest.makeSuite(testsFromCommandLine))

    # Include doctests in the Plugins Module
    suite.addTests( doctest.DocTestSuite(pynag.Plugins) )

    # Include doctests in the Parsers Module
    suite.addTests( doctest.DocTestSuite(pynag.Parsers) )

    # Include doctests in the Model Module
    suite.addTests( doctest.DocTestSuite(pynag.Model) )

    # Include doctests in the Utils Module
    suite.addTests( doctest.DocTestSuite(pynag.Utils) )

    return suite

if __name__ == '__main__':
    state = unittest.TextTestRunner().run( suite() )
    if state.failures or state.errors:
        sys.exit(1)
    sys.exit(0)
