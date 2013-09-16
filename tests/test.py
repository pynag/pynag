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

import unittest2 as unittest
import doctest
import tempfile
import shutil
import os
import sys
import string
import random

tests_dir = os.path.dirname(os.path.realpath(__file__))
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
        self.tmp_dir = tempfile.mkdtemp()  # Will be deleted after test runs
        #os.mkdir(self.tmp_dir)
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
        from pynag.Plugins import ok, warning, critical, unknown

        # 0 - return unknown on invalid input
        self.assertEqual(unknown, check_threshold(1, warning='invalid input'))

        # 1 - If no levels are specified, return OK
        self.assertEqual(ok, check_threshold(1))

        # 2 - If an ok level is specified and value is within range, return OK
        self.assertEqual(ok, check_threshold(1, ok="0..10"))
        self.assertEqual(ok, check_threshold(1, ok="0..10", warning="0..10"))
        self.assertEqual(ok, check_threshold(1, ok="0..10", critical="0..10"))

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
        """Test mk_livestatus integration"""
        livestatus = pynag.Parsers.mk_livestatus()
        requests = livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")

    def testConfig(self):
        """Test pynag.Parsers.config()"""
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
        """Test pynag.Parsers.object_cache"""
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertTrue(len(o.data.keys()) > 0, 'Object cache seems to be empty')

    def testConfig_backslash(self):
        """ Test parsing nagios object files with lines that end with backslash
        """
        c = pynag.Parsers.config()
        str1 = "define service {\nhost_name testhost\n}\n"
        str2 = "define service {\nhost_na\\\nme testhost\n}\n"

        parse1 = c.parse_string(str1)[0]
        parse2 = c.parse_string(str2)[0]

        # Remove metadata because stuff like line numbers has changed
        del parse1['meta']
        del parse2['meta']

        self.assertEqual(parse1, parse2)

    def testConfig_edit_static_file(self):
        """ Test pynag.Parsers.config._edit_static_file() """
        fd, filename = tempfile.mkstemp()
        c = pynag.Parsers.config(cfg_file=filename)

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

    def testLogFileParsing(self):
        expected_no_of_logentries = 63692
        expected_no_for_app01 = 127
        len_state_history = 14301
        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.cfg_file = "./nagios/nagios.cfg"
        l = pynag.Parsers.LogFiles(maincfg=pynag.Model.cfg_file)

        log = l.get_log_entries(start_time=0)
        self.assertEqual(expected_no_of_logentries, len(log))

        app01 = l.get_log_entries(start_time=0, host_name='app01.acme.com')
        self.assertEqual(expected_no_for_app01, len(app01))

        state_history = l.get_state_history(start_time=0)
        self.assertEqual(len_state_history, len(state_history))

    def testExtraOptsParser(self):
        """ Smoke-test Parsers.ExtraOptsParser """
        os.chdir(tests_dir)
        e = pynag.Parsers.ExtraOptsParser(section_name='main', config_file='dataset01/extraopts/other.ini')
        self.assertEqual('other.ini', e.get('filename'))

        # Test if default value works as expected:
        try:
            e.get('does not exist')
            self.assertTrue(False, "Code above should have raised an error")
        except ValueError:
            pass
        self.assertEqual("test", e.get('does not exist', "test"))

        # See if extraopts picks up on the NAGIOS_CONFIG_PATH variable
        os.environ['NAGIOS_CONFIG_PATH'] = "dataset01/extraopts/"
        e = pynag.Parsers.ExtraOptsParser(section_name='main')
        self.assertEqual('plugins.ini', e.get('filename'))

        # Using same config as above, test the getlist method
        self.assertEqual(['plugins.ini'], e.getlist('filename'))




class testModel(unittest.TestCase):
    """
    Basic Unit Tests that relate to saving objects
    """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        self.tmp_dir = tempfile.mkdtemp()  # Will be deleted after test runs

        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.cfg_file = "./nagios/nagios.cfg"
        pynag.Model.config = None
        pynag.Model.pynag_directory = self.tmp_dir
        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir', new_value=self.tmp_dir)

    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        pynag.Model.ObjectDefinition.objects.get_all()
        pynag.Model.config._edit_static_file(attribute='cfg_dir',old_value=self.tmp_dir,new_value=None)

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
        s2_expected = '%s/services/Servicewithhost_name.cfg' % pynag.Model.pynag_directory
        s3_expected = '%s/services/generic-test-service.cfg' % pynag.Model.pynag_directory

        self.assertEqual(s1_expected, s1.get_suggested_filename())
        self.assertEqual(s2_expected, s2.get_suggested_filename())
        self.assertEqual(s3_expected, s3.get_suggested_filename())

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
        s.set_attribute('check_command', check_command)

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
        self.assertEqual(sorted([service1, service2]), sorted(group.get_effective_services()))

    def testHostDelete(self):
        """ Create a test object and then delete it. """
        host = pynag.Model.Host()

        all_hosts = pynag.Model.Host.objects.get_all()
        all_hostnames = map(lambda x: x.host_name, all_hosts)

        # generate a random hostname for our new host
        chars = string.letters + string.digits
        host_name = "host-delete-test"  + ''.join([random.choice(chars) for i in xrange(10)])

        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(host_name not in all_hostnames)

        # Save our new host and reload our config if we somehow failed to create the
        # host we will get an exception here.
        host.host_name = host_name
        host.save()
        host = pynag.Model.Host.objects.get_by_shortname(host_name)

        # Host has been created. Lets delete it.
        host.delete()

        # Lets get all hosts again, and make sure the list is the same as when we started
        # If it is the same, the host was surely deleted
        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

    def testSaveNewObject(self):
        """ Test creating a new object with the model """
        hostname1 = "new_host1"
        hostname2 = "new_host2"

        # First of all, make sure the new hosts do not exist in the config before we save.
        hostlist1 = pynag.Model.Host.objects.filter(host_name=hostname1)
        hostlist2 = pynag.Model.Host.objects.filter(host_name=hostname2)

        self.assertEqual([], hostlist1)
        self.assertEqual([], hostlist2)

        # Save a new object, let pynag decide where it is saved.
        host = pynag.Model.Host(host_name=hostname1)
        host.save()
        hostlist1 = pynag.Model.Host.objects.filter(host_name=hostname1)
        self.assertEqual(1, len(hostlist1))

        # Save a new object, this time lets specify a filename for it
        host = pynag.Model.Host(host_name=hostname2)
        dest_dir = "%s/newhost2.cfg" % pynag.Model.pynag_directory
        host.set_filename(dest_dir)
        host.save()
        hostlist2 = pynag.Model.Host.objects.filter(host_name=hostname2)
        self.assertEqual(1, len(hostlist2))
        host = hostlist2[0]
        self.assertEqual(dest_dir, host.get_filename())

    def testMoveObject(self):
        """ Test ObjectDefinition.move() """

        file1 = pynag.Model.pynag_directory + "/file1.cfg"
        file2 = pynag.Model.pynag_directory + "/file2.cfg"
        host_name="movable_host"
        new_object = pynag.Model.Host(host_name=host_name)
        new_object.set_filename(file1)
        new_object.save()

        # Reload config, and see if new object is saved where we wanted it to be
        search_results = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertEqual(1, len(search_results))

        host = search_results[0]
        self.assertEqual(file1, host.get_filename())

        # Move the host to a new file and make sure it is moved.
        host.move(file2)

        search_results = pynag.Model.Host.objects.filter(host_name=host_name)
        self.assertEqual(1, len(search_results))

        host = search_results[0]
        self.assertEqual(file2, host.get_filename())

    def testMacroResolving(self):
        """ Test the get_macro and get_all_macros commands of services """

        service1 = pynag.Model.Service.objects.get_by_name('macroservice')
        macros = service1.get_all_macros()
        expected_macrokeys = ['$USER1$', '$ARG2$', '$_SERVICE_empty$', '$_HOST_nonexistant$', '$_SERVICE_nonexistant$', '$_SERVICE_macro1$', '$ARG1$', '$_HOST_macro1$', '$_HOST_empty$', '$HOSTADDRESS$', '$_SERVICE_not_used$']
        self.assertEqual(sorted(expected_macrokeys),  sorted(macros.keys()))

        self.assertEqual('/path/to/user1', macros['$USER1$'])
        self.assertEqual('/path/to/user1', macros['$ARG2$'])
        self.assertEqual('hostaddress', macros['$HOSTADDRESS$'])

        self.assertEqual('macro1', macros['$_SERVICE_macro1$'])
        self.assertEqual('macro1', macros['$ARG1$'])
        self.assertEqual('macro1', macros['$_HOST_macro1$'])
        self.assertEqual('this.macro.is.not.used', macros['$_SERVICE_not_used$'])

        self.assertEqual(None, macros['$_HOST_nonexistant$'])
        self.assertEqual(None, macros['$_SERVICE_nonexistant$'])

        self.assertEqual('', macros['$_SERVICE_empty$'])
        self.assertEqual('', macros['$_HOST_empty$'])

        expected_command_line = "/path/to/user1/macro -H 'hostaddress' host_empty='' service_empty='' host_macro1='macro1' arg1='macro1' host_nonexistant='' service_nonexistant='' escaped_dollarsign=$$ user1_as_argument=/path/to/user1"
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

        self.assertTrue(prod_api1 in hosts)  # prod-api-1 matches the regex
        self.assertTrue(prod_api2 in hosts)  # prod-api-2 matches the regex
        self.assertFalse(dev_api2 in hosts)  # dev-api-1 does not match

        # Hostgroup.get_effective_hosts() should match the same regex:
        self.assertEqual(hosts, prod_servers.get_effective_hosts())

    def test_rewrite(self):
        """ Test usage on ObjectDefinition.rewrite() """
        pass

    def test_attribute_is_empty(self):
        """Test if pynag properly determines if an attribute is empty"""

        #creating test object
        host =  pynag.Model.Host()
        host['host_name']   = "+"
        host['address']     = "not empty"
        host['contacts']    = "!"
        host['hostgroups']  = "                                             "
        host['contact_groups']="-"

        self.assertEqual(True,host.attribute_is_empty("host_name"))
        self.assertEqual(True,host.attribute_is_empty("contacts"))
        self.assertEqual(True,host.attribute_is_empty("hostgroups"))
        self.assertEqual(True,host.attribute_is_empty("contact_groups"))
        self.assertEqual(True,host.attribute_is_empty("_non_existing_attribute"))

        self.assertEqual(False,host.attribute_is_empty("address"))

    def test_contactgroup_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a contactgroup is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="del").save()
        hostesc_del2 = pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="del2").save()
        host         = pynag.Model.Host(          contacts="contact_STAYS", contact_groups=cg_name,      name="hoststay").save() 
        contact      = pynag.Model.Contact(       contactgroups=cg_name,                                 contact_name="contactstay").save()

        cg.delete(recursive=True,cleanup_related_items=True)
        
        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)
        
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.Host.objects.filter(name="hoststay")))
        self.assertTrue(pynag.Model.Host.objects.filter(name="hoststay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.Contact.objects.filter(contact_name="contactstay")))
        self.assertTrue(pynag.Model.Contact.objects.filter(contact_name="contactstay")[0].attribute_is_empty("contactgroups"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del2")))

    def test_contactgroup_delete_nonRecursive_cleanup(self):
        """Test if the right objects are _NOT_ removed when a contactgroup is deleted with recursive=False"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()

        cg.delete(recursive=False,cleanup_related_items=True)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups"))

    def test_contactgroup_delete_nonRecursive_nonCleanup(self):
        """Test if the no changes are made to related items if contactgroup is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=False) """

        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_nonRecursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()
        cg.delete(recursive=False,cleanup_related_items=False)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups"))

    def test_contactgroup_delete_recursive_nonCleanup(self):
        """Test if the no changes are made to related items if contactgroup is deleted - no deletion should happen even with recursive=True"""
        """ => test with delete(recursive=True,cleanup_related_items=False) """
        """ should have the same results as  test_contactgroup_delete_nonRecursive_nonCleanup()"""

        all_contactgroups = pynag.Model.Contactgroup.objects.get_all()
        all_contactgroup_names = map(lambda x: x.name, all_contactgroups)

        #creating test object
        chars = string.letters + string.digits
        cg_name = "cg_to_be_deleted_recursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        cg =  pynag.Model.Contactgroup()
        # Produce an error if our randomly generated contactgroup already exists in config
        self.assertTrue(cg_name not in all_contactgroup_names)
        cg['contactgroup_name']   = cg_name
        cg.save() # an object has to be saved before we can delete it!

        # since the contactgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contacts="contact_STAYS", contact_groups=cg_name,      name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(contacts=None,            contact_groups="+"+cg_name,  name="stay2").save()
        hostesc_stay3= pynag.Model.HostEscalation(contacts='',              contact_groups=cg_name,      name="stay3").save()

        cg.delete(recursive=True,cleanup_related_items=False)

        all_contactgroups_after_delete = pynag.Model.Contactgroup.objects.get_all()
        self.assertEqual(all_contactgroups,all_contactgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contact_groups"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contact_groups")) 

    def test_contact_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a contact is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="del").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="del2").save()
        contactGroup = pynag.Model.Contactgroup(  contactgroup_name="cgstay",          members=c_name                   ).save()

        c.delete(recursive=True,cleanup_related_items=True)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.Contactgroup.objects.filter(contactgroup_name="cgstay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("members"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del2")))

    def test_contact_delete_nonRecursive_cleanup(self):
        """Test if the right objects are _NOT_ removed when a contact is deleted with recursive=False"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()

        c.delete(recursive=False,cleanup_related_items=True)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_contact_delete_nonRecursive_nonCleanup(self):
        """Test if the no changes are made to related items if contact is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=False) """

        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_nonRecursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()
        c.delete(recursive=False,cleanup_related_items=False)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_contact_delete_recursive_nonCleanup(self):
        """Test if the no changes are made to related items if contact is deleted - no deletion should happen even with recursive=True"""
        """ => test with delete(recursive=True,cleanup_related_items=False) """
        """ should have the same results as  test_contact_delete_nonRecursive_nonCleanup()"""

        all_contacts = pynag.Model.Contact.objects.get_all()
        all_contact_names = map(lambda x: x.name, all_contacts)

        #creating test object
        chars = string.letters + string.digits
        c_name = "c_to_be_deleted_recursive_nonCleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        c =  pynag.Model.Contact()
        # Produce an error if our randomly generated contact already exists in config
        self.assertTrue(c_name not in all_contact_names)
        c['contact_name']   = c_name
        c.save() # an object has to be saved before we can delete it!

        # since the contact is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(contact_groups="contactgroup_STAYS", contacts=c_name,      name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(contact_groups=None,                 contacts="+"+c_name,  name="stay2").save()
        hostesc_del2 = pynag.Model.HostEscalation(contact_groups='',                   contacts=c_name,      name="stay3").save()

        c.delete(recursive=True,cleanup_related_items=False)

        all_contacts_after_delete = pynag.Model.Contact.objects.get_all()
        self.assertEqual(all_contacts,all_contacts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("contacts"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay3")))
        self.assertFalse(pynag.Model.HostEscalation.objects.filter(name="stay3")[0].attribute_is_empty("contacts"))

    def test_hostgroup_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a hostgroup is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_hostgroups = pynag.Model.Hostgroup.objects.get_all()
        all_hostgroup_names = map(lambda x: x.name, all_hostgroups)

        #creating test object
        chars = string.letters + string.digits
        hg_name = "hg_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        hg =  pynag.Model.Hostgroup()
        # Produce an error if our randomly generated hostgroup already exists in config
        self.assertTrue(hg_name not in all_hostgroup_names)
        hg['hostgroup_name']   = hg_name
        hg.save() # an object has to be saved before we can delete it!

        # since the hostgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(host_name="host_STAYS", hostgroup_name=hg_name,           name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(host_name=None,            hostgroup_name="+"+hg_name,         name="del").save()
        
        
        hostdep_stay = pynag.Model.HostDependency(host_name='host_STAYS',dependent_host_name="host_stays", hostgroup_name=hg_name, name="stay").save()
        hostdep_del  = pynag.Model.HostDependency(host_name='host_STAYS',dependent_hostgroup_name=hg_name,          name="del").save()
        hostdep_unrl = pynag.Model.HostDependency(dependent_host_name='foobar',hostgroup_name="unrelated_hg",    name="stays_because_its_not_related_to_deleted_hg").save()
        
        hoststay     = pynag.Model.Host(host_name="host_STAYS",    hostgroups=hg_name,                      name="hoststay").save()
        
        svcEscdel    = pynag.Model.ServiceEscalation(hostgroup_name=hg_name,                                name="svcEscdel").save()
        
        hg.delete(recursive=True,cleanup_related_items=True)

        all_hostgroups_after_delete = pynag.Model.Hostgroup.objects.get_all()
        self.assertEqual(all_hostgroups,all_hostgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))
        
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertEqual(0,len(pynag.Model.HostDependency.objects.filter(name="del")))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stays_because_its_not_related_to_deleted_hg")))
                
        self.assertEqual(1,len(pynag.Model.Host.objects.filter(name="hoststay")))
        self.assertTrue(pynag.Model.Host.objects.filter(name="hoststay")[0].attribute_is_empty("hostgroup_name"))
        
        self.assertEqual(0,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscdel")))

    def test_hostgroup_delete_nonRecursive_cleanup(self):
        """Test if the right objects are cleaned up when a hostgroup is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_hostgroups = pynag.Model.Hostgroup.objects.get_all()
        all_hostgroup_names = map(lambda x: x.name, all_hostgroups)

        #creating test object
        chars = string.letters + string.digits
        hg_name = "hg_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        hg =  pynag.Model.Hostgroup()
        # Produce an error if our randomly generated hostgroup already exists in config
        self.assertTrue(hg_name not in all_hostgroup_names)
        hg['hostgroup_name']   = hg_name
        hg.save() # an object has to be saved before we can delete it!

        # since the hostgroup is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(host_name="host_STAYS", hostgroup_name=hg_name,           name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(host_name=None,         hostgroup_name="+"+hg_name,       name="stay2").save()

        hostdep_stay = pynag.Model.HostDependency(host_name='host_STAYS',dependent_host_name="host_stays", hostgroup_name=hg_name, name="stay").save()
        hostdep_stay2= pynag.Model.HostDependency(host_name='host_STAYS',dependent_hostgroup_name=hg_name,                         name="stay2").save()

        svcEscstay    = pynag.Model.ServiceEscalation(hostgroup_name=hg_name,                                name="svcEscstay").save()

        hg.delete(recursive=False,cleanup_related_items=True)

        all_hostgroups_after_delete = pynag.Model.Hostgroup.objects.get_all()
        self.assertEqual(all_hostgroups,all_hostgroups_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("hostgroup_name"))
        
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay")[0].attribute_is_empty("hostgroup_name"))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay2")[0].attribute_is_empty("dependent_hostgroup_name"))

        self.assertEqual(1,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")))
        self.assertTrue(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")[0].attribute_is_empty("hostgroup_name"))

    def test_host_delete_recursive_cleanup(self):
        """Test if the right objects are removed when a host is deleted"""
        """ => test with delete(recursive=True,cleanup_related_items=True) """
        all_hosts = pynag.Model.Host.objects.get_all()
        all_host_names = map(lambda x: x.name, all_hosts)

        #creating test object
        chars = string.letters + string.digits
        h_name = "h_to_be_deleted_recursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        h =  pynag.Model.Host()
        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(h_name not in all_host_names)
        h['host_name']   = h_name
        h.save() # an object has to be saved before we can delete it!

        # since the host is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(hostgroup_name="hostgroup_STAYS", host_name=h_name,           name="stay").save()
        hostesc_del  = pynag.Model.HostEscalation(hostgroup_name=None,            host_name="+"+h_name,         name="del").save()


        hostdep_stay = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name="host_stays", host_name=h_name, name="stay").save()
        hostdep_del  = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name=h_name,          name="del").save()

        svcEscdel    = pynag.Model.ServiceEscalation(host_name=h_name,                                name="svcEscdel").save()

        h.delete(recursive=True,cleanup_related_items=True)

        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(0,len(pynag.Model.HostEscalation.objects.filter(name="del")))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertEqual(0,len(pynag.Model.HostDependency.objects.filter(name="del")))

        self.assertEqual(0,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscdel")))

    def test_host_delete_nonRecursive_cleanup(self):
        """Test if the right objects are cleaned up when a host is deleted"""
        """ => test with delete(recursive=False,cleanup_related_items=True) """
        all_hosts = pynag.Model.Host.objects.get_all()
        all_host_names = map(lambda x: x.name, all_hosts)

        #creating test object
        chars = string.letters + string.digits
        h_name = "h_to_be_deleted_nonRecursive_cleanup" + ''.join([random.choice(chars) for i in xrange(10)])
        h =  pynag.Model.Host()
        # Produce an error if our randomly generated host already exists in config
        self.assertTrue(h_name not in all_host_names)
        h['host_name']   = h_name
        h.save() # an object has to be saved before we can delete it!

        # since the host is unique as per the check above, the dependent escalations will consequently be unique as well
        hostesc_stay = pynag.Model.HostEscalation(hostgroup_name="hostgroup_STAYS", host_name=h_name,           name="stay").save()
        hostesc_stay2= pynag.Model.HostEscalation(hostgroup_name=None,         host_name="+"+h_name,       name="stay2").save()

        hostdep_stay = pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name="host_stays", host_name=h_name, name="stay").save()
        hostdep_stay2= pynag.Model.HostDependency(hostgroup_name='hostgroup_STAYS',dependent_host_name=h_name,                         name="stay2").save()

        svcEscstay    = pynag.Model.ServiceEscalation(host_name=h_name,                                name="svcEscstay").save()

        h.delete(recursive=False,cleanup_related_items=True)

        all_hosts_after_delete = pynag.Model.Host.objects.get_all()
        self.assertEqual(all_hosts,all_hosts_after_delete)

        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(1,len(pynag.Model.HostEscalation.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostEscalation.objects.filter(name="stay2")[0].attribute_is_empty("host_name"))

        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay")[0].attribute_is_empty("host_name"))
        self.assertEqual(1,len(pynag.Model.HostDependency.objects.filter(name="stay2")))
        self.assertTrue(pynag.Model.HostDependency.objects.filter(name="stay2")[0].attribute_is_empty("dependent_host_name"))

        self.assertEqual(1,len(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")))
        self.assertTrue(pynag.Model.ServiceEscalation.objects.filter(name="svcEscstay")[0].attribute_is_empty("host_name"))


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
            "%s update where nonexistantfield=test set nonexistentfield=pynag_unit_testing" % pynag_script,
            "%s config --get cfg_dir" % pynag_script,
        ]
        for i in ok_commands:
            exit_code, stdout, stderr = pynag.Utils.runCommand(i)
            self.assertEqual(0, exit_code, "Error when running command %s\nexit_code: %s\noutput: %s\nstderr: %s" % (i, exit_code, stdout, stderr))


def setUpParserDoctest(doctest):
    # The parser needs a Nagios config environment
    # we'll use dataset01 in the tests directory
    os.chdir(os.path.join(tests_dir, 'dataset01'))


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
    suite.addTests(doctest.DocTestSuite(pynag.Plugins))

    # Include doctests in the Parsers Module
    suite.addTests(doctest.DocTestSuite(pynag.Parsers, setUp=setUpParserDoctest))

    # Include doctests in the Model Module
    suite.addTests(doctest.DocTestSuite(pynag.Model))

    # Include doctests in the Utils Module
    suite.addTests(doctest.DocTestSuite(pynag.Utils))

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
    state = unittest.TextTestRunner().run(suite())
    if state.failures or state.errors:
        sys.exit(1)
    sys.exit(0)
