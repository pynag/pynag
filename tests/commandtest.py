import unittest
from mock import MagicMock, patch

try:
    # open_mock comes with mock 1.0.1
    from mock import mock_open
except ImportError:
    def mock_open(mock=None, data=None):
        file_spec = file
        if mock is None:
            mock = MagicMock(spec=file_spec)

        handle = MagicMock(spec=file_spec)
        handle.write.return_value = None
        if data is None:
            handle.__enter__.return_value = handle
        else:
            handle.__enter__.return_value = data
        mock.return_value = handle
        return mock

from pynag.Control import Command

class testCommandsToCommandFile(unittest.TestCase):
    def setUp(self):
        self.command_file = '/tmp/cmdfile'
        self.timestamp = 1368219495
        self.testhost = 'hosttest.example.com'
        self.testauthor = 'user@example.com'
        self.test_svc_desc = 'Test Service'
        self.test_svc_group = 'TestSVCGroup'
        self.test_check_command = 'test_check_command'
        self.test_event_handler_command = 'test_event_handler'
        self.check_interval = 50

        self.command = Command

        # Setup patching for open()
        self.command_open_mock = mock_open()
        self.patcher1 = patch('pynag.Control.Command.open', self.command_open_mock, create=True)
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_add_host_comment(self):
        persistent = 0
        comment = 'Test Comment!'
        self.command.add_host_comment(
                host_name=self.testhost,
                persistent=persistent,
                author=self.testauthor,
                comment=comment,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected_nagios_command = '[%s] ADD_HOST_COMMENT;%s;%s;%s;%s' % (self.timestamp, self.testhost, persistent, self.testauthor, comment)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected_nagios_command+'\n')

    """
    def test_shutdown_program(self):
        command = self.get_mock_command()
        command.shutdown_program(
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected_nagios_command = '[%s] SHUTDOWN_PROGRAM;' % self.timestamp
        command._write_to_command_file.assert_called_once_with(self.command_file, expected_nagios_command)
    """

    def test_shutdown_program(self):
        self.command.shutdown_program(
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] SHUTDOWN_PROGRAM;' % self.timestamp
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_disable_service_group_passive_svc_checks(self):
        self.command.disable_servicegroup_passive_svc_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_enable_service_group_passive_host_checks(self):
        self.command.enable_servicegroup_passive_host_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_disable_servicegroup_passive_host_checks(self):
        self.command.disable_servicegroup_passive_host_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_global_host_event_handler(self):
        self.command.change_global_host_event_handler(
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_GLOBAL_HOST_EVENT_HANDLER;%s' % (self.timestamp, self.test_event_handler_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_global_svc_event_handler(self):
        self.command.change_global_svc_event_handler(
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_GLOBAL_SVC_EVENT_HANDLER;%s' % (self.timestamp, self.test_event_handler_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_host_event_handler(self):
        self.command.change_host_event_handler(
                host_name=self.testhost,
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_HOST_EVENT_HANDLER;%s;%s' % (self.timestamp, self.testhost, self.test_event_handler_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')
        
    def test_change_svc_event_handler(self):
        self.command.change_svc_event_handler(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                event_handler_command= self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_SVC_EVENT_HANDLER;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.test_event_handler_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_host_check_command(self):
        self.command.change_host_check_command(
                host_name=self.testhost,
                check_command=self.test_check_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_HOST_CHECK_COMMAND;%s;%s' % (self.timestamp, self.testhost, self.test_check_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_svc_check_command(self):
        self.command.change_svc_check_command(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_command=self.test_check_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_SVC_CHECK_COMMAND;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.test_check_command)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_normal_host_check_interval(self):
        self.command.change_normal_host_check_interval(
                host_name=self.testhost,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_NORMAL_HOST_CHECK_INTERVAL;%s;%s' % (self.timestamp, self.testhost, self.check_interval)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_enable_svc_notifications(self):
        self.command.enable_svc_notifications(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] ENABLE_SVC_NOTIFICATIONS;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')
        
    def test_change_normal_svc_check_interval(self):
        self.command.change_normal_svc_check_interval(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_NORMAL_SVC_CHECK_INTERVAL;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.check_interval)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')
        
    def test_change_retry_svc_check_interval(self):
        self.command.change_retry_svc_check_interval(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_RETRY_SVC_CHECK_INTERVAL;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.check_interval)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')
        
    def test_change_max_host_check_attempts(self):
        max_attempts = 30
        self.command.change_max_host_check_attempts(
                host_name=self.testhost,
                check_attempts=max_attempts,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_MAX_HOST_CHECK_ATTEMPTS;%s;%s' % (self.timestamp, self.testhost, max_attempts)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_change_max_svc_check_attempts(self):
        max_attempts = 30
        self.command.change_max_svc_check_attempts(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_attempts=max_attempts,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_MAX_SVC_CHECK_ATTEMPTS;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, max_attempts)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')

    def test_process_service_check_result(self):
        return_code = 2
        plugin_output = 'output'
        self.command.process_service_check_result(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                return_code=return_code,
                plugin_output=plugin_output,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, return_code, plugin_output)
        self.command_open_mock.assert_called_with(self.command_file, 'a')
        handle = self.command_open_mock()
        handle.write.assert_called_once_with(expected + '\n')


class testCommandsToLivestatus(unittest.TestCase):
    def setUp(self):
        self.command_file = '/tmp/cmdfile'
        self.timestamp = 1368219495
        self.testhost = 'hosttest.example.com'
        self.testauthor = 'user@example.com'
        self.test_svc_desc = 'Test Service'
        self.test_svc_group = 'TestSVCGroup'
        self.test_host_group = 'TestHostGroup'
        self.test_check_command = 'test_check_command'
        self.test_event_handler_command = 'test_event_handler'
        self.check_interval = 50
    def tearDown(self):
        pass

    def get_mock_command(self):
        command = Command
        # Make writing to command file throw exception so we send to livestatus
        command._write_to_command_file = MagicMock(side_effect=Exception('Want to go to Livestatus'))
        command._write_to_livestatus = MagicMock()
        return command

    def test_process_host_check_result(self):
        command = self.get_mock_command()
        status_code = 2
        plugin_output = 'output'
        command.process_host_check_result(
                host_name=self.testhost,
                status_code=2,
                plugin_output=plugin_output,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] PROCESS_HOST_CHECK_RESULT;%s;%s;%s' % (self.timestamp, self.testhost, status_code, plugin_output)
        command._write_to_livestatus.assert_called_once_with(expected)
        
    def test_remove_host_acknowledgement(self):
        command = self.get_mock_command()
        command.remove_host_acknowledgement(
                host_name = self.testhost,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] REMOVE_HOST_ACKNOWLEDGEMENT;%s' % (self.timestamp, self.testhost)
        command._write_to_livestatus.assert_called_once_with(expected)
        
    def test_remove_svc_acknowledgement(self):
        command = self.get_mock_command()
        command.remove_svc_acknowledgement(
                host_name = self.testhost,
                service_description = self.test_svc_desc,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] REMOVE_SVC_ACKNOWLEDGEMENT;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_host_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_host_downtime(
                host_name = self.testhost,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_HOST_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.testhost,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)
                
    def test_schedule_svc_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_svc_downtime(
                host_name = self.testhost,
                service_description = self.test_svc_desc,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_SVC_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.testhost,
                self.test_svc_desc, start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)
                
    def test_disable_svc_notifications(self):
        command = self.get_mock_command()
        command.disable_svc_notifications(
                host_name = self.testhost,
                service_description = self.test_svc_desc,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] DISABLE_SVC_NOTIFICATIONS;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc)
        command._write_to_livestatus.assert_called_once_with(expected)

        
    def test_schedule_servicegroup_svc_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_servicegroup_svc_downtime(
                servicegroup_name = self.test_svc_group,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.test_svc_group,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_servicegroup_host_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_servicegroup_host_downtime(
                servicegroup_name = self.test_svc_group,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.test_svc_group,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_host_svc_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_host_svc_downtime(
                host_name = self.testhost,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_HOST_SVC_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.testhost,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_hostgroup_host_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_hostgroup_host_downtime(
                hostgroup_name = self.test_host_group,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_HOSTGROUP_HOST_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.test_host_group,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_hostgroup_svc_downtime(self):
        command = self.get_mock_command()
        start_time = self.timestamp + 1000
        end_time = self.timestamp + 2000
        fixed = 0
        trigger_id = 0
        duration = 0
        comment = 'Downtime!'
        command.schedule_hostgroup_svc_downtime(
                hostgroup_name = self.test_host_group,
                start_time = start_time,
                end_time = end_time,
                fixed = fixed,
                trigger_id = trigger_id,
                duration = duration,
                author = self.testauthor,
                comment = comment,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_HOSTGROUP_SVC_DOWNTIME;%s;%s;%s;%s;%s;%s;%s;%s' % (self.timestamp, self.test_host_group,
                start_time, end_time, fixed, trigger_id, duration, self.testauthor, comment)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_del_host_downtime(self):
        command = self.get_mock_command()
        downtime_id = 100
        command.del_host_downtime(
                downtime_id = downtime_id,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] DEL_HOST_DOWNTIME;%s' % (self.timestamp, downtime_id)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_del_svc_downtime(self):
        command = self.get_mock_command()
        downtime_id = 100
        command.del_svc_downtime(
                downtime_id = downtime_id,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] DEL_SVC_DOWNTIME;%s' % (self.timestamp, downtime_id)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_host_check(self):
        command = self.get_mock_command()
        command.schedule_host_check(
                host_name = self.testhost,
                check_time = self.timestamp,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_HOST_CHECK;%s;%s' % (self.timestamp, self.testhost, self.timestamp)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_forced_host_check(self):
        command = self.get_mock_command()
        command.schedule_forced_host_check(
                host_name = self.testhost,
                check_time = self.timestamp,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_FORCED_HOST_CHECK;%s;%s' % (self.timestamp, self.testhost, self.timestamp)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_forced_svc_check(self):
        command = self.get_mock_command()
        command.schedule_forced_svc_check(
                host_name = self.testhost,
                service_description = self.test_svc_desc,
                check_time = self.timestamp,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_FORCED_SVC_CHECK;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.timestamp)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_del_all_host_comments(self):
        command = self.get_mock_command()
        command.del_all_host_comments(
                host_name = self.testhost,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] DEL_ALL_HOST_COMMENTS;%s' % (self.timestamp, self.testhost)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_schedule_forced_host_svc_checks(self):
        command = self.get_mock_command()
        command.schedule_forced_host_svc_checks(
                host_name = self.testhost,
                check_time = self.timestamp,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] SCHEDULE_FORCED_HOST_SVC_CHECKS;%s;%s' % (self.timestamp, self.testhost, self.timestamp)
        command._write_to_livestatus.assert_called_once_with(expected)

    def test_process_file(self):
        command = self.get_mock_command()
        file_name = '/tmp/testfile'
        delete = 1
        command.process_file(
                file_name = file_name,
                delete = delete,
                command_file = self.command_file, timestamp = self.timestamp
            )
        expected = '[%s] PROCESS_FILE;%s;%s' % (self.timestamp, file_name, delete)
        command._write_to_livestatus.assert_called_once_with(expected)
