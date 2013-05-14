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
        pass


class testParsers(unittest.TestCase):
    def testLivestatus(self):
        "Test mk_livestatus integration"
        livestatus = pynag.Parsers.mk_livestatus()
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")
    def testConfig(self):
        "Test pynag.Parsers.config()"
        c = pynag.Parsers.config()
        c.parse()
        self.assertGreater(len(c.data), 0, "pynag.Parsers.config.parse() ran and afterwards we see no objects. Empty configuration?")
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
    def testObjectCache(self):
        "Test pynag.Parsers.object_cache"
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertGreater(len(o.data.keys()), 0, 'Object cache seems to be empty')
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

        s1_expected = '%s/services/Service without host_name.cfg' % pynag.Model.pynag_directory
        s2_expected = '%s/services/host.example.com/Service with host_name.cfg' % pynag.Model.pynag_directory
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
        self.assertEqual([service1,service2], group.get_effective_services())

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

    def test_rewrite(self):
        """ Test usage on ObjectDefinition.rewrite() """

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


class testUtils(unittest.TestCase):
    """ Collection of unittests for pynag.Utils module
    """
    def setUp(self):
        # Utils should work fine with just about any data, but lets use testdata01
        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.config = None
        pynag.Model.cfg_file = './nagios/nagios.cfg'
        s = pynag.Model.ObjectDefinition.objects.all
    def testCompareFilterWithGrep(self):
        """ test pynag.Utils.grep() by comparing it with pynag.Model.Service.objects.filter()

        # TODO: Currently  pynag.Model.Service.objects.filter() has some bugs, so some tests here fail.
        """
        result = self._compare_search_expressions(use='generic-service')

        result = self._compare_search_expressions(register=1,use='generic-service')

        result = self._compare_search_expressions(host_name__exists=True)

        result = self._compare_search_expressions(host_name__exists=False)

        result = self._compare_search_expressions(host_name__notcontains='l')

        result = self._compare_search_expressions(host_name__notcontains='this value cannot possibly exist')

        result = self._compare_search_expressions(host_name__startswith='l')

        result = self._compare_search_expressions(host_name__endswith='m')

        result = self._compare_search_expressions(host_name__isnot='examplehost for testing purposes')

    def testGrep(self):
        """ Test cases based on gradecke's testing """
        host = pynag.Model.string_to_class['host']()
        host['use'] = "generic-host"
        host['name'] = "ABC"
        host['_code'] = "ABC"
        host['_function'] = "Server,Production"

        host2 = pynag.Model.string_to_class['host']()
        host2['use'] = "generic-host"
        host2['name'] = "XYZ"
        host2['_code'] = "XYZ"
        host2['_function'] = "Switch,Production"

        hosts = host, host2

        result = pynag.Utils.grep(hosts, **{'_code__contains': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__contains': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'AB'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': True})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': False})
        self.assertEqual(0, len(result))

        result = pynag.Utils.grep(hosts, **{'_function__has_field': 'Server'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_function__has_field': 'Production'})
        self.assertEqual(2, len(result))


    def _compare_search_expressions(self, **expression):
        #print "Testing search expression %s" % expression
        all_services = pynag.Model.Service.objects.all
        result1 = pynag.Model.Service.objects.filter(**expression)
        result2 = pynag.Utils.grep(all_services, **expression)
        self.assertEqual(result1, result2,msg="Search output from pynag.Utils.grep() does not match pynag.Model.Service.objects.filter() when using parameters %s" % expression)
        return len(result1)

def suite():
    suite = unittest.TestSuite()

    # Include tests of Model
    suite.addTest(unittest.makeSuite(testModel))

    # Include tests of Parsers
    suite.addTest(unittest.makeSuite(testParsers))

    # Include tests of Plugins
    suite.addTest(unittest.makeSuite(testNewPluginThresholdSyntax))

    # Include tests of Utils
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

    return suite

if __name__ == '__main__':
    state = unittest.TextTestRunner().run( suite() )
    if state.failures or state.errors:
        sys.exit(1)
    sys.exit(0)
