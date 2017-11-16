from __future__ import absolute_import
__author__ = 'palli'

import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
import mock
import doctest
import tempfile
import shutil
import string
import random
import time
import datetime

from tests import tests_dir
import pynag.Parsers
import pynag.Utils.misc
import pynag.Parsers.main


class Config(unittest.TestCase):

    """ Test pynag.Parsers.config """

    def setUp(self):
        self.environment = pynag.Utils.misc.FakeNagiosEnvironment()
        self.environment.create_minimal_environment()

        self.tempdir = self.environment.tempdir
        self.config = self.environment.get_config()
        self.objects_file = self.environment.objects_dir + "/new_objects.cfg"

    def tearDown(self):
        self.environment.terminate()

    def test_parse(self):
        """ Smoketest config.parse() """
        self.config.parse()
        self.assertTrue(len(self.config.data) > 0, "pynag.Parsers.config.parse() ran and afterwards we see no objects. Empty configuration?")

    def test_parse_string_backslashes(self):
        """ Test parsing nagios object files with lines that end with backslash
        """
        c = self.config
        str1 = "define service {\nhost_name testhost\n}\n"
        str2 = "define service {\nhost_na\\\nme testhost\n}\n"

        parse1 = c.parse_string(str1)[0]
        parse2 = c.parse_string(str2)[0]

        # Remove metadata because stuff like line numbers has changed
        del parse1['meta']
        del parse2['meta']

        self.assertEqual(parse1, parse2)

    def test_edit_static_file(self):
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

    def test_item_add(self):
        filename = self.objects_file
        object_type = 'hostgroup'
        object_name = object_type + "-" + filename
        new_item = self.config.get_new_item(object_type, filename=filename)
        new_item['hostgroup_name'] = object_name
        self.config.item_add(new_item, filename=filename)
        self.config.parse()
        item_after_parse = self.config.get_hostgroup(object_name)
        del item_after_parse['meta']
        del new_item['meta']
        self.assertEqual(new_item, item_after_parse)

    def test_parse_string(self):
        """ test config.parse_string()
        """
        items = self.config.parse_string(minimal_config)
        self.assertEqual(
            items[11]['command_line'],
            '$USER1$/check_mrtgtraf -F $ARG1$ -a $ARG2$ -w $ARG3$ -c $ARG4$ -e $ARG5$'
        )
        self.assertEqual(
            items[11]['command_name'],
            'check_local_mrtgtraf'
        )

    def test_invalid_chars_in_item_edit(self):
        """ Test what happens when a user enters invalid characters attribute value """
        field_name = "test_field"
        field_value = "test_value"
        host_name = "ok_host"

        # Change field_name of our host
        self.config.parse()
        host = self.config.get_host(host_name)
        self.config.item_edit_field(host, field_name, field_value)

        # check if field_name matches what we saved it as
        self.config.parse()
        host = self.config.get_host(host_name)
        self.assertEqual(host.get(field_name), field_value)

        # Try to put new line as an attribute value:
        try:
            self.config.item_edit_field(host, field_name, "value with \n line breaks")
            self.assertEqual(False, True, "item_edit_field() should have raised an exception")
        except ValueError:
            self.assertEqual(True, True)

    def test_line_continuations(self):
        """ More tests for configs that have \ at an end of a line """
        definition = r"""
            define contactgroup {
            contactgroup_name portal-sms
            members \
            armin.gruner.sms, \

            }
            """
        with open(self.objects_file, 'a') as f:
            f.write(definition)
        c = self.config
        c.parse()
        item = c.get_object('contactgroup', 'portal-sms')
        self.assertTrue(item)
        # Change the members variable of our group, make sure the changes look ok
        c.item_edit_field(item, 'members', 'root')
        c.parse()
        item = c.get_object('contactgroup', 'portal-sms')

        self.assertTrue(item['members'] == 'root')
        self.assertFalse('armin.gruner.sms' in item['meta']['raw_definition'])

    def test_missing_end_of_object(self):
        """ Test parsing of a config with missing '}'
        """
        os.chdir(tests_dir)
        config = pynag.Parsers.Config()
        items = config.parse_file('dataset01/nagios/conf.d/missing.end.of.object.cfg')
        self.assertEqual(1, len(config.errors), "There should be exactly 1 config error")
        self.assertEqual(1, len(items), "there should be exactly 1 parsed items")


class ExtraOptsParser(unittest.TestCase):

    """ Test pynag.Parsers.ExtraOptsParser """

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

    @classmethod
    def setUpClass(cls):
        nagios = pynag.Utils.misc.FakeNagiosEnvironment()
        nagios.create_minimal_environment()
        nagios.configure_livestatus()
        nagios.start()
        cls.nagios = nagios
        cls.livestatus = nagios.livestatus_object

    @classmethod
    def tearDownClass(cls):
        cls.nagios.terminate()

    def testLivestatus(self):
        """ Smoketest livestatus integration """
        rows = self.livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(rows), "Could not get status.requests from livestatus")
        result = rows[0]
        self.assertEqual(['requests'], list(result.keys()))
        num_requests = result['requests']
        try:
            int(num_requests)
        except ValueError:
            self.assertTrue(False, "Expected requests to be a number")

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

    def testConnection(self):
        """ Test the livestatus.test() method """
        # Check if our newly created nagios environment has a working livestatus test:
        self.assertTrue(self.livestatus.test(), "Livestatus is supposed to work in FakeNagiosEnvironment")

        # Create a dummy livestatus instance and test connection to that:
        broken_livestatus = pynag.Parsers.Livestatus(livestatus_socket_path="does not exist")
        self.assertFalse(
            broken_livestatus.test(raise_error=False),
            "Dummy livestatus instance was supposed to be nonfunctional"
        )

    def test_raw_query_normal(self):
        result = self.livestatus.raw_query('GET status', 'Columns: requests')
        self.assertTrue(result.endswith('\n'))
        try:
            requests = int(result.strip())
        except ValueError:
            self.assertTrue(False, 'Expected livestatus result to be a number, but got %s' % repr(result))

    def test_write_normal(self):
        result = self.livestatus.write('GET status\nColumns: requests\n')
        self.assertTrue(result.endswith('\n'))
        try:
            requests = int(result.strip())
        except ValueError:
            self.assertTrue(False, 'Expected livestatus result to be a number, but got %s' % repr(result))

    @mock.patch('socket.socket')
    def test_write_raises(self, mock_socket_class):
        mock_socket = mock_socket_class.return_value
        mock_socket.send.side_effect = IOError

        # Make sure write() raises Livestatus errors if we cannot write to socket:
        with self.assertRaises(pynag.Parsers.LivestatusError):
            self.livestatus.write('GET status\nColumns: requests\n')

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_raw_query_calls_write(self, mock_write):
        result = self.livestatus.raw_query('GET services')

        # Make sure its returning the output of livestatus.write()
        self.assertEqual(mock_write.return_value, result)
        mock_write.assert_called_once_with('GET services\n')

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_raw_query_calls_write(self, mock_write):
        result = self.livestatus.raw_query('GET services', 'OutputFormat: python')

        # Make sure its returning the output of livestatus.write()
        self.assertEqual(mock_write.return_value, result)
        mock_write.assert_called_once_with('GET services\nOutputFormat: python\n\n')

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_retries_on_socket_error(self, mock_write):
        mock_write.side_effect = iter([pynag.Parsers.LivestatusError, '200'])
        self.livestatus.get_hosts()
        self.assertEqual(2, mock_write.call_count)

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_raises_on_repeated_errors(self, mock_write):
        mock_write.side_effect = iter([pynag.Parsers.LivestatusError, pynag.Parsers.LivestatusError, '200'])
        with self.assertRaises(pynag.Parsers.LivestatusError):
            self.livestatus.get_hosts()
        self.assertEqual(2, mock_write.call_count)

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_adds_required_headers(self, mock_write):
        result = self.livestatus.query('GET services')
        expected_query = 'GET services\nResponseHeader: fixed16\nOutputFormat: python\nColumnHeaders: on\n\n'
        mock_write.assert_called_once_with(expected_query)

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_adds_required_headers_authuser(self, mock_write):
        self.livestatus.authuser = 'nagiosadmin'
        self.livestatus.query('GET services')
        self.livestatus.authuser = None
        expected_query = 'GET services\nResponseHeader: fixed16\nOutputFormat: python\nColumnHeaders: on\n'
        expected_query += 'AuthUser: nagiosadmin\n\n'
        mock_write.assert_called_once_with(expected_query)

    def test_query_stats_have_no_headers(self):
        # Some versions of livestatus have an annoying bug that when you
        # include both Stats and ColumnHeaders: on, in a query, the output will get corrupted.
        # This test makes sure that livestatus.query() works around that bug.
        response = self.livestatus.query('GET services', 'Stats: state = 0', 'ColumnHeaders: on')
        self.assertIsInstance(response, list)
        self.assertEqual(1, len(response))
        stats_for_state_0 = response[0]
        self.assertIsInstance(stats_for_state_0, int)

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_empty_response_raises(self, mock_write):
        mock_write.return_value = ''
        with self.assertRaises(pynag.Parsers.InvalidResponseFromLivestatus):
            self.livestatus.query('GET services')

    @mock.patch('pynag.Parsers.Livestatus.write')
    def test_query_invalid_response_raises(self, mock_write):
        mock_write.return_value = '200\ngarbage data from livestatus['
        with self.assertRaises(pynag.Parsers.InvalidResponseFromLivestatus):
            self.livestatus.query('GET services')

    def test_query_outputformat_json_returns_string(self):
        result = self.livestatus.query('GET status', 'OutputFormat: json')
        self.assertIsInstance(result, str)

    def test_query_columheaders_off_returns_list_of_lists(self):
        result = self.livestatus.query('GET status', 'ColumnHeaders: off')
        for row in result:
            self.assertIsInstance(row, list)

    def test_query_invalid_query_raises(self):
        with self.assertRaises(pynag.Parsers.LivestatusError):
            self.livestatus.query('GET something else')

    def test_parse_response_header_empty(self):
        with self.assertRaises(pynag.Parsers.LivestatusError):
            self.livestatus._parse_response_header('')

    def test_parse_response_header_ok(self):
        header = '200      510608'
        data = '[[1,2,3]]'
        result = self.livestatus._parse_response_header(header + '\n' + data)
        self.assertEqual(data, result)

    def test_parse_response_header_problem(self):
        header = '600'
        data = '[[1,2,3]]'
        with self.assertRaises(pynag.Parsers.LivestatusError):
            self.livestatus._parse_response_header(header + '\n' + data)


class LivestatusQuery(unittest.TestCase):

    def setUp(self):
        self.query = pynag.Parsers.LivestatusQuery('GET services')

    def test_init_normal(self):
        test_query = 'GET status\nColumns: requests\n\n'
        query = pynag.Parsers.LivestatusQuery(test_query)
        self.assertEqual(test_query, query.get_query())

    def test_init_with_args(self):
        test_query = 'GET status\nColumns: requests\n\n'
        query = pynag.Parsers.LivestatusQuery('GET status', 'Columns: requests')
        self.assertEqual(test_query, query.get_query())

    def test_init_with_kwargs(self):
        test_query = 'GET hosts\nColumns: name\nFilter: name = localhost\n\n'
        query = pynag.Parsers.LivestatusQuery('GET hosts', 'Columns: name', name='localhost')
        self.assertEqual(test_query, query.get_query())

    def test_add_header(self):
        self.query.add_header('OutputFormat', 'python')

        expected_result = 'GET services\nOutputFormat: python\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test_add_header_line(self):
        self.query.add_header_line('OutputFormat: python')

        expected_result = 'GET services\nOutputFormat: python\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test_remove_header(self):
        self.query.add_header_line('OutputFormat: python')
        self.query.remove_header('OutputFormat')

        expected_result = 'GET services\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test_set_outputformat(self):
        self.query.set_outputformat('python')
        expected_result = 'GET services\nOutputFormat: python\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test_set_responseheader(self):
        self.query.set_responseheader('fixed16')
        expected_result = 'GET services\nResponseHeader: fixed16\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test_has_header_true(self):
        self.query.add_header('OutputFormat', 'python')
        self.assertTrue(self.query.has_header('OutputFormat'))

    def test_has_header_false(self):
        self.assertFalse(self.query.has_header('OutputFormat'))

    def test_set_authuser(self):
        self.query.set_authuser('username')
        expected_result = 'GET services\nAuthUser: username\n\n'
        self.assertEqual(expected_result, self.query.get_query())

    def test__str__(self):
        query = str(self.query)
        self.assertEqual('GET services\n\n', query)


class ObjectCache(unittest.TestCase):

    """ Tests for pynag.Parsers.objectcache
    """
    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testObjectCache(self):
        """Test pynag.Parsers.object_cache"""
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertTrue(len(list(o.data.keys())) > 0, 'Object cache seems to be empty')


class LogFiles(unittest.TestCase):

    """ Test pynag.Parsers.LogFiles
    """

    def setUp(self):
        os.chdir(tests_dir)
        os.chdir('dataset01')
        cfg_file = "./nagios/nagios.cfg"
        self.log = pynag.Parsers.LogFiles(maincfg=cfg_file)

    def testLogFileParsing(self):
        expected_no_of_logentries = 1040
        expected_no_for_app01 = 11
        len_state_history = 1030

        log = self.log.get_log_entries(start_time=0)
        self.assertEqual(expected_no_of_logentries, len(log))

        app01 = self.log.get_log_entries(start_time=0, host_name='app01.acme.com')
        self.assertEqual(expected_no_for_app01, len(app01))

        state_history = self.log.get_state_history(start_time=0)
        self.assertEqual(len_state_history, len(state_history))

    def testGetLogFiles(self):
        files_num = 0
        for root, dirs, files in os.walk("nagios/log"):
            files_num += len(files)

        expected_number_of_files = files_num
        logfiles = self.log.get_logfiles()
        self.assertTrue('./nagios/log/nagios.log' in logfiles)
        self.assertEqual(5, len(logfiles))

    def testLogEntriesAreSorted(self):
        entries = self.log.get_log_entries(start_time=0)
        last_timestamp = -1
        for entry in entries:
            current_timestamp = entry.get('time')
            if last_timestamp >= 0 and last_timestamp > current_timestamp:
                message = "Timestamp of log entries are not in ascending order"
                self.assertLessEqual(last_timestamp, current_timestamp, message)
            last_timestamp = current_timestamp

    def testForMissingLogEntries(self):
        # Get all log files from 2014-01-01, make sure we find all of them
        start_time = (2014, 0o1, 0o1, 0, 0, 0, 0, 0, 0)
        start_time = time.mktime(start_time)  # timestamp

        # We expect 1020 log entries to appear
        # nagios.log + 2 logfiles for 2014.
        # All log files from 2013 should be skipped
        expected_number_of_entries = 1000 + 10 + 10
        entries = self.log.get_log_entries(start_time=start_time)
        self.assertEqual(expected_number_of_entries, len(entries))

    def testGetLogFilesSkipsDirectories(self):
        directory = './nagios/log/archives/old'
        self.assertNotIn(directory, self.log.get_logfiles())


class Status(unittest.TestCase):

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


class MultiSite(Livestatus):

    """ Tests for pynag.Parsers.MultiSite
    """

    def testAddBackend(self):
        livestatus = pynag.Parsers.MultiSite()
        backend1 = "local autodiscovered"
        backend2 = "local autodiscovered2"

        # Add a backend, and make sure we are getting hosts out of it
        livestatus.add_backend(path=self.nagios.livestatus_socket_path, name=backend1)
        hosts = livestatus.get_hosts()
        self.assertTrue(len(hosts) > 0)

        # Add the same backend under a new name, and check if number of hosts
        # doubles
        livestatus.add_backend(path=self.nagios.livestatus_socket_path, name=backend2)
        hosts2 = livestatus.get_hosts()
        self.assertEqual(len(hosts) * 2, len(hosts2))

        # Get hosts from one specific backend
        hosts_backend1 = livestatus.get_hosts(backend=backend1)
        hosts_backend2 = livestatus.get_hosts(backend=backend2)

        self.assertEqual(len(hosts), len(hosts_backend1))


@unittest.skip("Not ready for production yet")
class SshConfig(Config):

    def setUp(self):
        self.instance = pynag.Parsers.SshConfig(host="localhost", username='palli')

    def tearDown(self):
        pass

    def testParseMaincfg(self):
        self.instance.parse_maincfg()

    def testParse(self):
        self.instance.parse()
        host = self.instance.get_host('localhost')
        self.instance.item_edit_field(host, '__test', host['__test'] + '+')

    def testOpenFile(self):
        self.instance.open('/etc/nagios3/nagios.cfg').read()

    def testPathWrappers(self):
        """ Test our os.path wrappers
        """
        ftp = self.instance.ftp
        i = ftp.stat('/')
        self.assertTrue(self.instance.isdir('/'))


class MainConfigTest(unittest.TestCase):

    def setUp(self):
        os.chdir(tests_dir)
        os.chdir('dataset01')
        cfg_file = "./nagios/nagios.cfg"
        self.main_config = pynag.Parsers.main.MainConfig(filename=cfg_file)

    def test_normal(self):
        self.assertEqual('test.cfg', self.main_config.get('cfg_file'))
        self.assertEqual(['test.cfg'], self.main_config.get_list('cfg_file'))

    def test_parse_string_normal(self):
        result = self.main_config._parse_string('cfg_file=test.cfg')
        self.assertEqual([('cfg_file', 'test.cfg')], result)

    def test_parse_string_empty_line(self):
        result = self.main_config._parse_string('#empty\n\n#line')
        self.assertEqual([], result)

    def test_parse_string_skips_comments(self):
        result = self.main_config._parse_string('# this is a comment')
        self.assertEqual([], result)

minimal_config = r"""
define timeperiod {
  alias                          24 Hours A Day, 7 Days A Week
  friday          00:00-24:00
  monday          00:00-24:00
  saturday        00:00-24:00
  sunday          00:00-24:00
  thursday        00:00-24:00
  timeperiod_name                24x7
  tuesday         00:00-24:00
  wednesday       00:00-24:00
}

define timeperiod {
  alias                          24x7 Sans Holidays
  friday          00:00-24:00
  monday          00:00-24:00
  saturday        00:00-24:00
  sunday          00:00-24:00
  thursday        00:00-24:00
  timeperiod_name                24x7_sans_holidays
  tuesday         00:00-24:00
  use		us-holidays		; Get holiday exceptions from other timeperiod
  wednesday       00:00-24:00
}

define contactgroup {
  alias                          Nagios Administrators
  contactgroup_name              admins
  members                        nagiosadmin
}

define command {
  command_line                   $USER1$/check_ping -H $HOSTADDRESS$ -w 3000.0,80% -c 5000.0,100% -p 5
  command_name                   check-host-alive
}

define command {
  command_line                   $USER1$/check_dhcp $ARG1$
  command_name                   check_dhcp
}

define command {
  command_line                   $USER1$/check_ftp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_ftp
}

define command {
  command_line                   $USER1$/check_hpjd -H $HOSTADDRESS$ $ARG1$
  command_name                   check_hpjd
}

define command {
  command_line                   $USER1$/check_http -I $HOSTADDRESS$ $ARG1$
  command_name                   check_http
}

define command {
  command_line                   $USER1$/check_imap -H $HOSTADDRESS$ $ARG1$
  command_name                   check_imap
}

define command {
  command_line                   $USER1$/check_disk -w $ARG1$ -c $ARG2$ -p $ARG3$
  command_name                   check_local_disk
}

define command {
  command_line                   $USER1$/check_load -w $ARG1$ -c $ARG2$
  command_name                   check_local_load
}

define command {
  command_line                   $USER1$/check_mrtgtraf -F $ARG1$ -a $ARG2$ -w $ARG3$ -c $ARG4$ -e $ARG5$
  command_name                   check_local_mrtgtraf
}

define command {
  command_line                   $USER1$/check_procs -w $ARG1$ -c $ARG2$ -s $ARG3$
  command_name                   check_local_procs
}

define command {
  command_line                   $USER1$/check_swap -w $ARG1$ -c $ARG2$
  command_name                   check_local_swap
}

define command {
  command_line                   $USER1$/check_users -w $ARG1$ -c $ARG2$
  command_name                   check_local_users
}

define command {
  command_line                   $USER1$/check_nt -H $HOSTADDRESS$ -p 12489 -v $ARG1$ $ARG2$
  command_name                   check_nt
}

define command {
  command_line                   $USER1$/check_ping -H $HOSTADDRESS$ -w $ARG1$ -c $ARG2$ -p 5
  command_name                   check_ping
}

define command {
  command_line                   $USER1$/check_pop -H $HOSTADDRESS$ $ARG1$
  command_name                   check_pop
}

define command {
  command_line                   $USER1$/check_smtp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_smtp
}

define command {
  command_line                   $USER1$/check_snmp -H $HOSTADDRESS$ $ARG1$
  command_name                   check_snmp
}

define command {
  command_line                   $USER1$/check_ssh $ARG1$ $HOSTADDRESS$
  command_name                   check_ssh
}

define command {
  command_line                   $USER1$/check_tcp -H $HOSTADDRESS$ -p $ARG1$ $ARG2$
  command_name                   check_tcp
}

define command {
  command_line                   $USER1$/check_udp -H $HOSTADDRESS$ -p $ARG1$ $ARG2$
  command_name                   check_udp
}

define contact {
  name                           generic-contact
  host_notification_commands     notify-host-by-email
  host_notification_options      d,u,r,f,s
  host_notification_period       24x7
  register                       0
  service_notification_commands  notify-service-by-email
  service_notification_options   w,u,c,r,f,s
  service_notification_period    24x7
}

define host {
  name                           generic-host
  event_handler_enabled          1
  failure_prediction_enabled     1
  flap_detection_enabled         1
  notification_period            24x7
  notifications_enabled          1
  process_perf_data              1
  register                       0
  retain_nonstatus_information   1
  retain_status_information      1
}

define host {
  name                           generic-printer
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            workhours
  register                       0
  retry_interval                 1
  statusmap_image                printer.png
}

define host {
  name                           generic-router
  use                            generic-switch
  register                       0
  statusmap_image                router.png
}

define service {
  name                           generic-service
  action_url                     /pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$
  active_checks_enabled          1
  check_freshness                0
  check_period                   24x7
  event_handler_enabled          1
  failure_prediction_enabled     1
  flap_detection_enabled         1
  icon_image                     unknown.gif
  is_volatile                    0
  max_check_attempts             3
  normal_check_interval          10
  notes_url                      /adagios/objectbrowser/edit_object/object_type=service/shortname=$HOSTNAME$/$SERVICEDESC$
  notification_interval          60
  notification_options           w,u,c,r
  notification_period            24x7
  notifications_enabled          1
  obsess_over_service            1
  parallelize_check              1
  passive_checks_enabled         1
  process_perf_data              1
  register                       0
  retain_nonstatus_information   1
  retain_status_information      1
  retry_check_interval           2
}

define host {
  name                           generic-switch
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            24x7
  register                       0
  retry_interval                 1
  statusmap_image                switch.png
}

define host {
  name                           linux-server
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  max_check_attempts             10
  notification_interval          120
  notification_options           d,u,r
  notification_period            workhours
  register                       0
  retry_interval                 1
}

define service {
  name                           local-service
  use                            generic-service
  max_check_attempts             4
  normal_check_interval          5
  register                       0
  retry_check_interval           1
}

define contact {
  use                            generic-contact
  alias                          Nagios Admin
  contact_name                   nagiosadmin
  email                          nagios@localhost
}

define timeperiod {
  alias                          No Time Is A Good Time
  timeperiod_name                none
}

define command {
  command_line                   /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\nHost: $HOSTNAME$\nState: $HOSTSTATE$\nAddress: $HOSTADDRESS$\nInfo: $HOSTOUTPUT$\n\nDate/Time: $LONGDATETIME$\n" | /bin/mail -s "** $NOTIFICATIONTYPE$ Host Alert: $HOSTNAME$ is $HOSTSTATE$ **" $CONTACTEMAIL$
  command_name                   notify-host-by-email
}

define command {
  command_line                   /usr/bin/printf "%b" "***** Nagios *****\n\nNotification Type: $NOTIFICATIONTYPE$\n\nService: $SERVICEDESC$\nHost: $HOSTALIAS$\nAddress: $HOSTADDRESS$\nState: $SERVICESTATE$\n\nDate/Time: $LONGDATETIME$\n\nAdditional Info:\n\n$SERVICEOUTPUT$\n" | /bin/mail -s "** $NOTIFICATIONTYPE$ Service Alert: $HOSTALIAS$/$SERVICEDESC$ is $SERVICESTATE$ **" $CONTACTEMAIL$
  command_name                   notify-service-by-email
}

define command {
  command_line                   /usr/bin/printf "%b" "$LASTHOSTCHECK$\t$HOSTNAME$\t$HOSTSTATE$\t$HOSTATTEMPT$\t$HOSTSTATETYPE$\t$HOSTEXECUTIONTIME$\t$HOSTOUTPUT$\t$HOSTPERFDATA$\n" >> /var/log/nagios/host-perfdata.out
  command_name                   process-host-perfdata
}

define command {
  command_line                   /usr/bin/printf "%b" "$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICESTATE$\t$SERVICEATTEMPT$\t$SERVICESTATETYPE$\t$SERVICEEXECUTIONTIME$\t$SERVICELATENCY$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$\n" >> /var/log/nagios/service-perfdata.out
  command_name                   process-service-perfdata
}

define timeperiod {
  alias                          U.S. Holidays
  december 25             00:00-00:00     ; Christmas
  january 1               00:00-00:00     ; New Years
  july 4                  00:00-00:00     ; Independence Day
  monday -1 may           00:00-00:00     ; Memorial Day (last Monday in May)
  monday 1 september      00:00-00:00     ; Labor Day (first Monday in September)
  name			us-holidays
  thursday 4 november     00:00-00:00     ; Thanksgiving (4th Thursday in November)
  timeperiod_name                us-holidays
}

define host {
  name                           windows-server
  use                            generic-host
  check_command                  check-host-alive
  check_interval                 5
  check_period                   24x7
  contact_groups                 admins
  hostgroups
  max_check_attempts             10
  notification_interval          30
  notification_options           d,r
  notification_period            24x7
  register                       0
  retry_interval                 1
}

define hostgroup {
  alias                          Windows Servers
  hostgroup_name                 windows-servers
}

define timeperiod {
  alias                          Normal Work Hours
  friday		09:00-17:00
  monday		09:00-17:00
  thursday	09:00-17:00
  timeperiod_name                workhours
  tuesday		09:00-17:00
  wednesday	09:00-17:00
}

define command {
    command_name	check_dummy
    command_line	$USER1$/check_dummy!$ARG1$!$ARG2$
}


define host {
    host_name		ok_host
    use			generic-host
    address			ok_host
    max_check_attempts	1
    check_command		check_dummy!0!Everything seems to be okay
}


define service {
    host_name		ok_host
    use			generic-service
    service_description	ok service 1
    check_command		check_dummy!0!Everything seems to be okay
}

"""


if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
