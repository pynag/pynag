# -*- coding: utf-8 -*-

""" miscellaneous utils classes and function.

 The reason they don't live in in pynag.Utils is that they have more requirements, and they do on occation import
 pynag.Model og pynag.Parsers
"""


from __future__ import absolute_import
import tempfile
import os
import time
import pynag.Parsers.config_parser
import pynag.Parsers.livestatus
import pynag.Model
import six

from pynag.errors import PynagError
from pynag.Utils import bytes2str


class MiscError(PynagError):
    """Base class for errors in this module."""


class SandboxError(MiscError):
    """Raised when FakeEnvironment tries to modify files outside its sandbox."""


class FakeNagiosEnvironment(object):

    """ Creates a fake nagios environment with minimal configs in /tmp/

    Example:
        >>> nagios = FakeNagiosEnvironment()
        >>> nagios.create_minimal_environment()  # Create temporary director with minimal config
        >>> nagios.update_model()  # Update the global variables in pynag.Model
        >>> nagios.configure_livestatus()  # Configure a livestatus socket
        >>> result, stdout, stderr = nagios.start()  # Start up nagios
        >>> config = nagios.get_config()   # Returns config_parser.Config instance
        >>> livestatus = nagios.get_livestatus()  # Returns livestatus.Livestatus instance
        >>> result, stdout, sdterr = nagios.stop()  # Stop nagios
        >>> nagios.terminate()  # Stops nagios and cleans up everything

    """

    def __init__(self, global_config_file=None, p1_file=None, livestatus=False):
        self.global_config_file = global_config_file
        self.p1_file = p1_file
        self._model_is_dirty = False
        self.livestatus_module_path = livestatus
        self.livestatus_object = None
        self.config = None

        self.tempdir = tempfile.mkdtemp('nagios-environment')
        path_to_socket = os.path.join(self.tempdir, "livestatus.socket")
        self.livestatus_socket_path = path_to_socket

    def get_config(self):
        if not self.config:
            self.create_minimal_environment()
        return self.config

    def get_livestatus(self):
        if not self.livestatus_object:
            self.configure_livestatus()
        return self.livestatus_object

    def update_model(self):
        """ Update the global variables in pynag.Model to point to our config """
        self.original_objects_dir = pynag.Model.pynag_directory
        self.original_cfg_file = pynag.Model.cfg_file
        self.original_config = pynag.Model.config

        pynag.Model.config = self.get_config()
        pynag.Model.cfg_file = self.config.cfg_file
        pynag.Model.pynag_directory = self.objects_dir
        pynag.Model.eventhandlers = []

        self._model_is_dirty = True

    def open_decorator(self, func):
        """ Safety decorator aroundaround self.config.open()

         It wraps around self.config.open() and raises error if the fake
         nagios environment tries to open file outside the sandbox.
        """
        def wrap(filename, *args, **kwargs):
            if filename.startswith(self.tempdir):
                return func(filename, *args, **kwargs)
            else:
                raise SandboxError("FakeNagiosEnvironment tried to open file outside its sandbox: %s" % (filename, ))
        wrap.__name__ = func.__name__
        wrap.__module__ = func.__module__
        return wrap

    def restore_model(self):
        """ Restores the global variables in pynag.Model """
        pynag.Model.config = self.original_config
        pynag.Model.cfg_file = self.original_cfg_file
        pynag.Model.pynag_directory = self.original_objects_dir
        self._model_is_dirty = False

    def create_minimal_environment(self):
        """ Starts a nagios server with empty config in an isolated environment """
        t = self.tempdir
        cfg_file = self.cfg_file = os.path.join(t, "nagios.cfg")
        open(cfg_file, 'w').write('')

        objects_dir = self.objects_dir = os.path.join(t, "conf.d")
        os.mkdir(objects_dir)

        check_result_path = os.path.join(self.tempdir, 'checkresults')
        os.mkdir(check_result_path)

        log_dir = os.path.join(self.tempdir, 'log')
        archive_dir = os.path.join(log_dir, 'archive')
        os.mkdir(log_dir)
        os.mkdir(archive_dir)

        with open(objects_dir + "/minimal_config.cfg", 'w') as f:
            f.write(minimal_config)

        config = self.config = pynag.Parsers.config_parser.Config(cfg_file=cfg_file)
        self.config.open = self.open_decorator(self.config.open)
        config.parse()
        config._edit_static_file(attribute='log_archive_path',
                                 new_value=os.path.join(t, "log/archive"))
        config._edit_static_file(attribute='log_file',
                                 new_value=os.path.join(t, "log/nagios.log"))
        config._edit_static_file(attribute='object_cache_file',
                                 new_value=os.path.join(t, "objects.cache"))
        config._edit_static_file(attribute='precached_object_file',
                                 new_value=os.path.join(t, "/objects.precache"))
        config._edit_static_file(attribute='lock_file',
                                 new_value=os.path.join(t, "nagios.pid"))
        config._edit_static_file(attribute='command_file',
                                 new_value=os.path.join(t, "nagios.cmd"))
        config._edit_static_file(attribute='state_retention_file',
                                 new_value=os.path.join(t, "retention.dat"))
        config._edit_static_file(attribute='status_file',
                                 new_value=os.path.join(t, "status.dat"))
        config._edit_static_file(attribute='cfg_dir', new_value=objects_dir)
        config._edit_static_file(attribute='log_initial_states',
                                 new_value="1")
        config._edit_static_file(attribute='enable_embedded_perl',
                                 new_value='0')
        config._edit_static_file(attribute='event_broker_options',
                                 new_value='-1')
        config._edit_static_file(attribute='illegal_macro_output_chars',
                                 new_value='''~$&|<>''')
        config._edit_static_file(attribute='check_result_path',
                                 new_value=check_result_path)
        config._edit_static_file(attribute='temp_path', new_value=log_dir)
        config._edit_static_file(attribute='temp_file',
                                 new_value=os.path.join(t, "nagios.tmp"))

    def clean_up(self):
        """ Clean up all temporary directories """
        command = ['rm', '-rf', self.tempdir]
        pynag.Utils.runCommand(command=command, shell=False)

    def terminate(self):
        """ Stop the nagios environment and remove all temporary files """
        self.stop()
        if self._model_is_dirty:
            self.restore_model()
        self.clean_up()
        time.sleep(.2)

    def start(self, start_command=None, timeout=10):
        self.configure_p1_file()
        start_command = bytes2str(start_command)
        if not start_command:
            nagios_binary = self.config.guess_nagios_binary()
            start_command = "%s -d %s" % (nagios_binary, self.config.cfg_file)
        result = pynag.Utils.runCommand(command=start_command)
        code, stdout, stderr = result

        pid_file = os.path.join(self.tempdir, "nagios.pid")
        while not os.path.exists(pid_file) and timeout:
            timeout -= 1
            time.sleep(1)

        start_error = None
        if not os.path.exists(pid_file):
            start_error = "Nagios pid file did not materialize"
        if result[0] != 0:
            start_error = "Nagios did not start, bad return code"

        if start_error:
            if os.path.exists(os.path.join(self.tempdir, "nagios.log")):
                log_file_output = open(os.path.join(self.tempdir, "nagios.log")).read()
            else:
                log_file_output = "No log file found."
            message = start_error
            message += "Command: {start_command}\n"
            message += "Exit Code: {code}\n"
            message += "============\nStandard out\n{stdout}\n"
            message += "=============\nStandard Err\n{stderr}\n"
            message += "=============\nLog File output\n{log_file_output}\n"
            message = message.format(**locals())
            raise Exception(message)
        time.sleep(.2)
        return result

    def stop(self, stop_command=None):
        pid_file = os.path.join(self.tempdir, "nagios.pid")
        if not os.path.exists(pid_file):
            return
        pid = open(pid_file).read()

        if not stop_command:
            stop_command = "kill -9 %s" % pid
        result = pynag.Utils.runCommand(stop_command)
        time.sleep(.2)
        return result

    def configure_livestatus(self):
        if not self.livestatus_module_path:
            self.livestatus_module_path = self.guess_livestatus_path()
        line = "%s %s" % (self.livestatus_module_path, self.livestatus_socket_path)
        config = self.get_config()
        config._edit_static_file(attribute="broker_module", new_value=line)
        self.livestatus_object = pynag.Parsers.livestatus.Livestatus(
            nagios_cfg_file=config.cfg_file,
        )

    def guess_p1_file(self):
        global_config = pynag.Parsers.config_parser.Config(cfg_file=self.global_config_file)
        global_config.parse_maincfg()
        for k, v in global_config.maincfg_values:
            if k == 'p1_file':
                return v

    def configure_p1_file(self):
        if not self.p1_file:
            self.p1_file = self.guess_p1_file()
        config = self.get_config()
        config._edit_static_file(attribute='p1_file', new_value=self.p1_file)

    def guess_livestatus_path(self):
        """ Tries to guess a path to mk-livestatus

        Returns:
            string containing full path to mk-livestatus broker_module
        """
        # Find mk_livestatus broker module
        global_config = pynag.Parsers.config_parser.Config(cfg_file=self.global_config_file)
        global_config.parse_maincfg()
        for k, v in global_config.maincfg_values:
            if k == 'broker_module' and 'livestatus' in v:
                livestatus_module = v.split()[0]
                return livestatus_module

    def import_config(self, path):
        """ Copies any file or directory into our environment and include it in object configuration

        Args:
            path:   full path to a nagios cfg file or a directory of cfg files

        Raises:
            Exception if path is not found
        """
        destination = self.objects_dir
        command = "cp -r '{path}' '{destination}/'".format(**locals())
        return os.system(command)


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
      max_check_attempts             3
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
      alias                 Normal Work Hours
      friday                09:00-17:00
      monday                09:00-17:00
      thursday              09:00-17:00
      timeperiod_name       workhours
      tuesday               09:00-17:00
      wednesday             09:00-17:00
    }

    define command {
        command_name    check_dummy
        command_line    $USER1$/check_dummy!$ARG1$!$ARG2$
    }


    define host {
        host_name           ok_host
        use                 generic-host
        address	            ok_host
        max_check_attempts	1
        check_command       check_dummy!0!Everything seems to be okay
    }


    define service {
        host_name           ok_host
        use                 generic-service
        service_description ok service 1
        check_command       check_dummy!0!Everything seems to be okay
    }

    """
