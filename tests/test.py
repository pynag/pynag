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

try:
    import unittest2 as unittest
except ImportError:
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

# skipIf workaround for python < 2.7
try:
    from unittest import skipIf
except ImportError:
    def skipIf(condition, message):
        def decorator(f):
            return None if condition else f
        return decorator
    unittest.skipIf = skipIf

class testDatasetParsing(unittest.TestCase):
    """ Parse any dataset in the tests directory starting with "testdata" """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        os.chdir(tests_dir)
        self.tmp_dir = tempfile.mkdtemp() # Will be deleted after test runs
        #os.mkdir(self.tmp_dir)
        pynag.Model.pynag_directory = self.tmp_dir
    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir,ignore_errors=True)
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

class testNewPluginThresholdSyntax(unittest.TestCase):
    """ Unit tests for pynag.Plugins.new_threshold_syntax """
    def test_check_threshold(self):
        """ Test check_threshold() with different parameters

        Returns (in order of appearance):
        0 - Unknown on invalid input
        1 - If no levels are specified, return OK
        2 - If an ok level is specified and value is within range, return OK
        3 - If a critical level is specified and value is within range, return CRITICAL
        4 - If a warning level is specified and value is within range, return WARNING
        5 - If an ok level is specified, return CRITICAL
        6 - Otherwise return OK
        """
        from pynag.Plugins.new_threshold_syntax import check_threshold
        from pynag.Plugins import ok,warning,critical,unknown


        # 0 - return unknown on invalid input
        self.assertEqual(unknown, check_threshold(1, warning='invalid input'))

        # 1 - If no levels are specified, return OK
        self.assertEqual(ok, check_threshold(1))



        # 2 - If an ok level is specified and value is within range, return OK
        self.assertEqual(ok, check_threshold(1, ok="0..10"))
        self.assertEqual(ok, check_threshold(1, ok="0..10",warning="0..10"))
        self.assertEqual(ok, check_threshold(1, ok="0..10",critical="0..10"))

        # 3 - If a critical level is specified and value is within range, return CRITICAL
        self.assertEqual(critical, check_threshold(1, critical="0..10"))

        # 4 - If a warning level is specified and value is within range, return WARNING
        self.assertEqual(warning, check_threshold(1, warning="0..10"))

        # 5 - If an ok level is specified, return CRITICAL
        self.assertEqual(critical, check_threshold(1, ok="10..20"))

        # 6 - Otherwise return OK
        # ... we pass only warning, then only critical, then both, but value is always outside ranges
        self.assertEqual(ok, check_threshold(1, warning="10..20"))
        self.assertEqual(ok, check_threshold(1, critical="10..20"))
        self.assertEqual(ok, check_threshold(1, warning="10..20", critical="20..30"))
        

    def test_invalid_range(self):
        from pynag.Plugins.new_threshold_syntax import check_range
        from pynag.Utils import PynagError

        self.assertRaises(PynagError, check_range, 1, '')
        self.assertRaises(PynagError, check_range, 1, None)

    def test_invalid_threshold(self):
        from pynag.Plugins.new_threshold_syntax import parse_threshold
        from pynag.Utils import PynagError

        self.assertRaises(PynagError, parse_threshold, '')
        self.assertRaises(AttributeError, parse_threshold, None)
        self.assertRaises(PynagError, parse_threshold, 'string')

class testParsers(unittest.TestCase):
    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testLivestatus(self):
        "Test mk_livestatus integration"
        livestatus = pynag.Parsers.mk_livestatus()
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")
    def testConfig(self):
        "Test pynag.Parsers.config()"
        c = pynag.Parsers.config()
        c.parse()
        self.assertTrue(len(c.data) > 0, "pynag.Parsers.config.parse() ran and afterwards we see no objects. Empty configuration?")
    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testStatus(self):
        """Unit test for pynag.Parsers.status()"""
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
    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testObjectCache(self):
        "Test pynag.Parsers.object_cache"
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertTrue(len(o.data.keys()) > 0, 'Object cache seems to be empty')
    def testConfig_edit_static_file(self):
        """ Test pynag.Parsers.config._edit_static_file() """
        fd,filename = tempfile.mkstemp()
        c  = pynag.Parsers.config(cfg_file=filename)

        # Lets add some attributes to our new file
        c._edit_static_file(attribute='first', new_value='first_test')
        c._edit_static_file(attribute='appended', new_value='first_append', append=True)
        c._edit_static_file(attribute='appended', new_value='second_append', append=True)
        c._edit_static_file(attribute='appended', new_value='third_append', append=True)

        c.parse_maincfg()

        # Sanity check, are our newly added attributes in the file
        self.assertEqual('first_test', c.get_cfg_value('first'))
        self.assertEqual('first_append', c.get_cfg_value('appended'))
        self.assertEqual(None, c.get_cfg_value('non_existant_value'))

        # Make some changes, see if everything is still as it is supposed to
        c._edit_static_file(attribute='first', new_value='first_test_changed')
        c._edit_static_file(attribute='appended', old_value='second_append', new_value='second_append_changed')

        c.parse_maincfg()
        self.assertEqual('first_test_changed', c.get_cfg_value('first'))
        self.assertEqual('first_append', c.get_cfg_value('appended'))

        # Try a removal
        c._edit_static_file(attribute='appended', old_value='first_append', new_value=None)
        c.parse_maincfg()

        # first append should be gone, and second one should be changed:
        self.assertEqual('second_append_changed', c.get_cfg_value('appended'))

        os.remove(filename)

class testModel(unittest.TestCase):
    """
    Basic Unit Tests that relate to saving objects
    """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        self.tmp_dir = tempfile.mkdtemp() # Will be deleted after test runs

        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.cfg_file = "./nagios/nagios.cfg"
        pynag.Model.config = None
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

        s1_expected = '%s/services/Servicewithouthost_name.cfg' % pynag.Model.pynag_directory
        s2_expected = '%s/hosts/host.example.com.cfg' % pynag.Model.pynag_directory
        s3_expected = '%s/services/generic-test-service.cfg' % pynag.Model.pynag_directory

        self.assertEqual(s1_expected, s1.get_suggested_filename() )
        self.assertEqual(s2_expected, s2.get_suggested_filename() )
        self.assertEqual(s3_expected, s3.get_suggested_filename() )

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
    def testServicegroupMembership(self):
        """ Loads servicegroup definitions from testdata01 and checks if get_effective_services works as expected
        """

        # service1 and service2 should both belong to group but they are defined differently
        group = pynag.Model.Servicegroup.objects.get_by_shortname('group-2')
        service1 = pynag.Model.Service.objects.get_by_shortname('node-1/cpu')
        service2 = pynag.Model.Service.objects.get_by_shortname('node-1/cpu2')
        self.assertEqual([group], service1.get_effective_servicegroups())
        self.assertEqual([group], service2.get_effective_servicegroups())
        self.assertEqual(sorted([service1,service2]), sorted(group.get_effective_services()))

    def testMacroResolving(self):
        """ Test the get_macro and get_all_macros commands of services """

        service1 = pynag.Model.Service.objects.get_by_name('macroservice')
        macros = service1.get_all_macros()
        expected_macrokeys = ['$USER1$', '$ARG2$', '$_SERVICE_empty$', '$_HOST_nonexistant$', '$_SERVICE_nonexistant$', '$_SERVICE_macro1$', '$ARG1$', '$_HOST_macro1$', '$_HOST_empty$', '$HOSTADDRESS$', '$_SERVICE_not_used$']
        self.assertEqual(sorted(expected_macrokeys),  sorted(macros.keys()))

        self.assertEqual('/path/to/user1',macros['$USER1$'])
        self.assertEqual('/path/to/user1',macros['$ARG2$'])
        self.assertEqual('hostaddress',macros['$HOSTADDRESS$'])

        self.assertEqual('macro1',macros['$_SERVICE_macro1$'])
        self.assertEqual('macro1',macros['$ARG1$'])
        self.assertEqual('macro1',macros['$_HOST_macro1$'])
        self.assertEqual('this.macro.is.not.used',macros['$_SERVICE_not_used$'])

        self.assertEqual(None,macros['$_HOST_nonexistant$'])
        self.assertEqual(None,macros['$_SERVICE_nonexistant$'])

        self.assertEqual('',macros['$_SERVICE_empty$'])
        self.assertEqual('',macros['$_HOST_empty$'])

        expected_command_line= "/path/to/user1/macro -H 'hostaddress' host_empty='' service_empty='' host_macro1='macro1' arg1='macro1' host_nonexistant='' service_nonexistant='' escaped_dollarsign=$$ user1_as_argument=/path/to/user1"
        actual_command_line = service1.get_effective_command_line()

        self.assertEqual(expected_command_line, actual_command_line)

    def testParenting(self):
        """ Test the use of get_effective_parents and get_effective_children
        """

        # Get host named child, check its parents
        h = pynag.Model.Host.objects.get_by_name('child')
        expected_result = ['parent01', 'parent02', 'parent-of-all']
        hosts = h.get_effective_parents(recursive=True)
        host_names = map(lambda x: x.name, hosts)
        self.assertEqual(expected_result, host_names)

        # Get host named parent-of-all, get its children
        h = pynag.Model.Host.objects.get_by_name('parent-of-all')
        expected_result = ['parent01', 'parent02', 'parent03', 'child']
        hosts = h.get_effective_children(recursive=True)
        host_names = map(lambda x: x.name, hosts)
        self.assertEqual(expected_result, host_names)

    def test_hostgroup_with_regex_members(self):
        """ Test parsing a hostgroup with regex members. """
        prod_servers = pynag.Model.Hostgroup.objects.get_by_shortname('prod-servers')
        # prod_server.members = "prod-[a-zA-Z0-9]+"

        prod_api1 = pynag.Model.Host.objects.get_by_shortname('prod-api-1')
        prod_api2 = pynag.Model.Host.objects.get_by_shortname('prod-api-2')
        dev_api2 = pynag.Model.Host.objects.get_by_shortname('dev-api-1')

        service = pynag.Model.Service.objects.get_by_name('short-term-load')
        hosts = service.get_effective_hosts()

        self.assertTrue(prod_api1 in hosts) # prod-api-1 matches the regex
        self.assertTrue(prod_api2 in hosts) # prod-api-2 matches the regex
        self.assertFalse(dev_api2 in hosts) # dev-api-1 does not match

        # Hostgroup.get_effective_hosts() should match the same regex:
        self.assertEqual(hosts, prod_servers.get_effective_hosts())

    def test_rewrite(self):
        """ Test usage on ObjectDefinition.rewrite() """
        pass

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

    # Include tests of Plugins
    from tests.plugintest import testPlugin, testPluginNoThreshold, testPluginHelper, testPluginParams
    suite.addTest(unittest.makeSuite(testPlugin))
    suite.addTest(unittest.makeSuite(testPluginNoThreshold))
    suite.addTest(unittest.makeSuite(testPluginHelper))
    suite.addTest(unittest.makeSuite(testNewPluginThresholdSyntax))
    suite.addTest(unittest.makeSuite(testPluginParams))

    # Include tests of Utils
    from tests.utilstest import testUtils
    suite.addTest(unittest.makeSuite(testUtils))

    # Include tests of Dataset parsing
    suite.addTest(unittest.makeSuite(testDatasetParsing))

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

    from tests.commandtest import testCommandsToCommandFile, testCommandsToLivestatus
    suite.addTest(unittest.makeSuite(testCommandsToCommandFile))
    suite.addTest(unittest.makeSuite(testCommandsToLivestatus))

    from tests.controltest import testControl
    suite.addTest(unittest.makeSuite(testControl))

    # Test defaultdict clone, tests borrowed from Python 2.7 upstream
    from tests.test_defaultdict import TestDefaultDict
    suite.addTest(unittest.makeSuite(TestDefaultDict))

    return suite

if __name__ == '__main__':
    state = unittest.TextTestRunner().run( suite() )
    if state.failures or state.errors:
        sys.exit(1)
    sys.exit(0)
