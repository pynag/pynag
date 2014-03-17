__author__ = 'palli'
import unittest2 as unittest
import doctest
import tempfile
import shutil
import os
import sys
import string
import random

import pynag.Parsers
from tests import tests_dir


class testParsers(unittest.TestCase):

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
    def testParseMaincfg(self):
        """ Test parsing of different broker_module declarations """
        path = "/var/lib/nagios/rw/livestatus"  # Path to the livestatus socket

        # Test plain setup with no weird arguments
        fd, filename = tempfile.mkstemp()
        os.write(fd, 'broker_module=./livestatus.o /var/lib/nagios/rw/livestatus')
        status = pynag.Parsers.mk_livestatus(nagios_cfg_file=filename)
        self.assertEqual(path, status.livestatus_socket_path)
        os.close(fd)

        # Test what happens if arguments are provided
        fd, filename = tempfile.mkstemp()
        os.write(fd, 'broker_module=./livestatus.o /var/lib/nagios/rw/livestatus hostgroups=t')
        status = pynag.Parsers.mk_livestatus(nagios_cfg_file=filename)
        self.assertEqual(path, status.livestatus_socket_path)
        os.close(fd)

        # Test what happens if arguments are provided before and after file socket path
        fd, filename = tempfile.mkstemp()
        os.write(fd, 'broker_module=./livestatus.o  num_client_threads=20 /var/lib/nagios/rw/livestatus hostgroups=t')
        status = pynag.Parsers.mk_livestatus(nagios_cfg_file=filename)
        self.assertEqual(path, status.livestatus_socket_path)
        os.close(fd)

        # Test what happens if livestatus socket path cannot be found
        try:
            fd, filename = tempfile.mkstemp()
            os.write(fd, 'broker_module=./livestatus.o  num_client_threads=20')
            status = pynag.Parsers.mk_livestatus(nagios_cfg_file=filename)
            self.assertEqual(path, status.livestatus_socket_path)
            os.close(fd)
            self.assertEqual(True, "Above could should have raised exception")
        except pynag.Parsers.ParserError:
            pass


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
        cfg_file = "./nagios/nagios.cfg"
        l = pynag.Parsers.LogFiles(maincfg=cfg_file)

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

class Livestatus(unittest.TestCase):
    def setUp(self):
        cfg_file = None
        self.livestatus = pynag.Parsers.mk_livestatus(nagios_cfg_file=cfg_file)

    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testLivestatus(self):
        """ Smoketest livestatus integration """
        requests = self.livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")
