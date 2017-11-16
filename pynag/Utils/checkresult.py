# !/usr/bin/python
#
# NagiosCheckResult- Class that creates Nagios checkresult file and
# writes Passive Host and Service checks to it
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import os
import tempfile
import time

service_state = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']
host_state = ['UP', 'DOWN', 'DOWN', 'DOWN']


class CheckResult(object):

    """
    Methods for creating host and service checkresults for nagios processing
    """

    def __init__(self, nagios_result_dir, file_time=None):

        if file_time is not None:
            self.file_time = file_time
        else:
            self.file_time = time.time()

        # Nagios is quite fussy about the filename, it must be
        # a 7 character name starting with 'c'

        self.fh, self.cmd_file = tempfile.mkstemp(prefix='c',
                                                  dir=nagios_result_dir)

        os.write(self.fh, "### Active Check Result File ###\n")
        os.write(self.fh, "file_time=" + str(self.file_time) + "\n")

    def service_result(self, host_name, service_description, **kwargs):
        """
        Create a service checkresult

        Any kwarg will be added to the checkresult

        Args:
            host_name (str)
            service_descritpion (str)
        Kwargs:
            check_type (int): active(0) or passive(1)
            check_options (int)
            scheduled_check (int)
            reschedule_check (int)
            latency (float)
            start_time (float)
            finish_time (float)
            early_timeout (int)
            exited_ok (int)
            return_code (int)
            output (str): plugin output
        """
        kwargs.update({
            'host_name': host_name,
            'service_description': service_description
        })
        return self.__output_result(**kwargs)

    def host_result(self, host_name, **kwargs):
        """
        Create a service checkresult

        Any kwarg will be added to the checkresult

        Args:
            host_name (str)
            service_descritpion (str)
        Kwargs:
            check_type (int): active(0) or passive(1)
            check_options (int)
            scheduled_check (int)
            reschedule_check (int)
            latency (float)
            start_time (float)
            finish_time (float)
            early_timeout (int)
            exited_ok (int)
            return_code (int)
            output (str): plugin output
        """
        kwargs.update({
            'host_name': host_name,
        })
        return self.__output_result(**kwargs)

    def __output_result(self, **kwargs):
        """
        Create a checkresult

        Kwargs:
            host_name (str)
            service_descritpion (str)
            check_type (int): active(0) or passive(1)
            check_options (int)
            scheduled_check (int)
            reschedule_check (int)
            latency (float)
            start_time (float)
            finish_time (float)
            early_timeout (int)
            exited_ok (int)
            return_code (int)
            output (str): plugin output
        """
        parms = {
            'check_type': 0,  # Active
            'check_options': 0,
            'scheduled_check': 0,
            'reschedule_check': 0,
            'latency': 0.0,
            'start_time': time.time(),
            'finish_time': time.time(),
            'early_timeout': 0,
            'exited_ok': 0,
            'return_code': 0
        }
        parms.update(**kwargs)

        object_type = 'host'
        if 'service_description' in parms:
            object_type = 'service'

        if 'output' not in parms:
            if object_type == 'host':
                parms['output'] = host_state[int(parms['return_code'])]
            else:
                parms['output'] = service_state[int(parms['return_code'])]

        parms['output'].replace('\n', '\\n')
        os.write(self.fh, """
### Nagios {1} Check Result ###
# Time: {0}\n""".format(self.file_time, object_type.capitalize()))
        for key, value in list(parms.items()):
            os.write(self.fh, key + "=" + str(value) + "\n")

    def submit(self):
        """Submits the results to nagios"""
        os.close(self.fh)
        ok_filename = self.cmd_file + ".ok"
        ok_fh = file(ok_filename, 'a')
        ok_fh.close()
        return self.cmd_file
