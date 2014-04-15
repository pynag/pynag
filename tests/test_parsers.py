__author__ = 'palli'

import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
import doctest
import tempfile
import shutil
import string
import random

from tests import tests_dir
import pynag.Parsers
import pynag.Utils.misc

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
        self.assertEqual(items[11]['command_line'], '$USER1$/check_mrtgtraf -F $ARG1$ -a $ARG2$ -w $ARG3$ -c $ARG4$ -e $ARG5$')
        self.assertEqual(items[11]['command_name'], 'check_local_mrtgtraf')
    
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
    def setUp(self):
        cfg_file = None
        self.livestatus = pynag.Parsers.mk_livestatus(nagios_cfg_file=cfg_file)

    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testLivestatus(self):
        """ Smoketest livestatus integration """
        requests = self.livestatus.query('GET status', 'Columns: requests')
        self.assertEqual(1, len(requests), "Could not get status.requests from livestatus")

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


class ObjectCache(unittest.TestCase):
    """ Tests for pynag.Parsers.objectcache
    """
    @unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
    def testObjectCache(self):
        """Test pynag.Parsers.object_cache"""
        o = pynag.Parsers.object_cache()
        o.parse()
        self.assertTrue(len(o.data.keys()) > 0, 'Object cache seems to be empty')


class LogFiles(unittest.TestCase):
    """ Test pynag.Parsers.LogFiles
    """
    def setUp(self):
        os.chdir(tests_dir)
        os.chdir('dataset01')
        cfg_file = "./nagios/nagios.cfg"
        self.log = pynag.Parsers.LogFiles(maincfg=cfg_file)

    def testLogFileParsing(self):
        expected_no_of_logentries = 63692
        expected_no_for_app01 = 127
        len_state_history = 14301

        log = self.log.get_log_entries(start_time=0)
        self.assertEqual(expected_no_of_logentries, len(log))

        app01 = self.log.get_log_entries(start_time=0, host_name='app01.acme.com')
        self.assertEqual(expected_no_for_app01, len(app01))

        state_history = self.log.get_state_history(start_time=0)
        self.assertEqual(len_state_history, len(state_history))

    def testGetLogFiles(self):
        logfiles = self.log.get_logfiles()
        self.assertEqual(2, len(logfiles))
        self.assertEqual('./nagios/log/nagios.log', logfiles[0])
        self.assertEqual('./nagios/log/archives/archivelog1.log', logfiles[1])


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

@unittest.skipIf(os.getenv('TRAVIS', None) == 'true', "Running in Travis")
class MultiSite(Livestatus):
    """ Tests for pynag.Parsers.MultiSite
    """
    def testAddBackend(self):
        livestatus = pynag.Parsers.MultiSite()
        backend1 = "local autodiscovered"
        backend2 = "local autodiscovered2"

        # Add a backend, and make sure we are getting hosts out of it
        livestatus.add_backend(path=None, name=backend1)
        hosts = livestatus.get_hosts()
        self.assertTrue(len(hosts) > 0)

        # Add the same backend under a new name, and check if number of hosts
        # doubles
        livestatus.add_backend(path=None, name=backend2)
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
        print host['__test']
        self.instance.item_edit_field(host, '__test', host['__test'] + '+')

    def testOpenFile(self):
        self.instance.open('/etc/nagios3/nagios.cfg').read()

    def testPathWrappers(self):
        """ Test our os.path wrappers
        """
        ftp = self.instance.ftp
        i = ftp.stat('/')
        self.assertTrue(self.instance.isdir('/'))



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
