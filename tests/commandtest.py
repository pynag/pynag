import unittest
from mock import MagicMock

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
    def tearDown(self):
        pass

    def getMockCommand(self):
        command = Command
        command._write_to_command_file = MagicMock()
        return command

    def testAddHostComment(self):
        command = self.getMockCommand()
        persistent = 0
        comment = 'Test Comment!'
        command.add_host_comment(
                host_name=self.testhost,
                persistent=persistent,
                author=self.testauthor,
                comment=comment,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected_nagios_command = '[%s] ADD_HOST_COMMENT;%s;%s;%s;%s' % (self.timestamp, self.testhost, persistent, self.testauthor, comment)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected_nagios_command)

    def testShutdownProgram(self):
        command = self.getMockCommand()
        command.shutdown_program(
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected_nagios_command = '[%s] SHUTDOWN_PROGRAM;' % self.timestamp
        command._write_to_command_file.assert_called_once_with(self.command_file, expected_nagios_command)

    def testDisableServiceGroupPassiveSvcChecks(self):
        command = self.getMockCommand()
        command.disable_servicegroup_passive_svc_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testEnableServiceGroupPassiveHostChecks(self):
        command = self.getMockCommand()
        command.enable_servicegroup_passive_host_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testDisableServicegroupPassiveHostChecks(self):
        command = self.getMockCommand()
        command.disable_servicegroup_passive_host_checks(
                servicegroup_name=self.test_svc_group,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;%s' % (self.timestamp, self.test_svc_group)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeGlobalHostEventHandler(self):
        command = self.getMockCommand()
        command.change_global_host_event_handler(
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_GLOBAL_HOST_EVENT_HANDLER;%s' % (self.timestamp, self.test_event_handler_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeGlobalSvcEventHandler(self):
        command = self.getMockCommand()
        command.change_global_svc_event_handler(
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_GLOBAL_SVC_EVENT_HANDLER;%s' % (self.timestamp, self.test_event_handler_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeHostEventHandler(self):
        command = self.getMockCommand()
        command.change_host_event_handler(
                host_name=self.testhost,
                event_handler_command=self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_HOST_EVENT_HANDLER;%s;%s' % (self.timestamp, self.testhost, self.test_event_handler_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)
        
    def testChangeSvcEventHandler(self):
        command = self.getMockCommand()
        command.change_svc_event_handler(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                event_handler_command= self.test_event_handler_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_SVC_EVENT_HANDLER;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.test_event_handler_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeHostCheckCommand(self):
        command = self.getMockCommand()
        command.change_host_check_command(
                host_name=self.testhost,
                check_command=self.test_check_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_HOST_CHECK_COMMAND;%s;%s' % (self.timestamp, self.testhost, self.test_check_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeSvcCheckCommand(self):
        command = self.getMockCommand()
        command.change_svc_check_command(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_command=self.test_check_command,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_SVC_CHECK_COMMAND;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.test_check_command)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeNormalHostCheckInterval(self):
        command = self.getMockCommand()
        command.change_normal_host_check_interval(
                host_name=self.testhost,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_NORMAL_HOST_CHECK_INTERVAL;%s;%s' % (self.timestamp, self.testhost, self.check_interval)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testEnableSvcNotifications(self):
        command = self.getMockCommand()
        command.enable_svc_notifications(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] ENABLE_SVC_NOTIFICATIONS;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)
        
    def testChangeNormalSvcCheckInterval(self):
        command = self.getMockCommand()
        command.change_normal_svc_check_interval(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_NORMAL_SVC_CHECK_INTERVAL;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.check_interval)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)
        
    def testChangeRetrySvcCheckInterval(self):
        command = self.getMockCommand()
        command.change_retry_svc_check_interval(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_interval=self.check_interval,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_RETRY_SVC_CHECK_INTERVAL;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, self.check_interval)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)
        
    def testChangeMaxHostCheckAttempts(self):
        command = self.getMockCommand()
        max_attempts = 30
        command.change_max_host_check_attempts(
                host_name=self.testhost,
                check_attempts=max_attempts,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_MAX_HOST_CHECK_ATTEMPTS;%s;%s' % (self.timestamp, self.testhost, max_attempts)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testChangeMaxSvcCheckAttempts(self):
        command = self.getMockCommand()
        max_attempts = 30
        command.change_max_svc_check_attempts(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                check_attempts=max_attempts,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] CHANGE_MAX_SVC_CHECK_ATTEMPTS;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, max_attempts)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)

    def testProcessServiceCheckResult(self):
        command = self.getMockCommand()
        return_code = 2
        plugin_output = 'output'
        command.process_service_check_result(
                host_name=self.testhost,
                service_description=self.test_svc_desc,
                return_code=return_code,
                plugin_output=plugin_output,
                command_file=self.command_file, timestamp=self.timestamp
            )
        expected = '[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s' % (self.timestamp, self.testhost, self.test_svc_desc, return_code, plugin_output)
        command._write_to_command_file.assert_called_once_with(self.command_file, expected)


class testCommandsToLivestatus(unittest.TestCase):
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
    def tearDown(self):
        pass

    def getMockCommand(self):
        command = Command
        # Make writing to command file throw exception so we send to livestatus
        command._write_to_command_file = MagicMock(side_effect=Exception('Want to go to Livestatus'))
        command._write_to_livestatus = MagicMock()
        return command

    def testProcessHostCheckResult(self):
        command = self.getMockCommand()
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
        
