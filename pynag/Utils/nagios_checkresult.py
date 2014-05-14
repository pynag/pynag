#!/usr/bin/python
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
###########################################################################

import os
import tempfile
import time
import sys


class GenerateNagiosCheckResult:
    
    def __init__(self):
	self.service_state = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
	self.host_state = {0: 'UP', 1: 'DOWN', 2: 'DOWN', 3: 'DOWN'}

    # Creates a checkresult file
    def create(self, nagios_result_dir):
	# Nagios is quite fussy about the filename, it must be
        # a 7 character name starting with 'c'
	try:
		tmp_file = tempfile.mkstemp(prefix='c',dir=nagios_result_dir) # specifies name and directory, check tempfile thoroughly
		self.fh = tmp_file[0]
        	self.cmd_file = tmp_file[1]
        	os.write(self.fh, "### Active Check Result File ###\n")
        	os.write(self.fh, "file_time=" + str(int(time.time())) + "\n")
	except OSError as e:
    		#print "OS error({0}): {1}".format(e.errno, e.strerror)
		print "Failed to create tempfile at", nagios_result_dir
		sys.exit(1)
        
    # Accepts parameters required for the host checkresult
    # Writes host checks to checkresult file
    def build_host(self, host, check_type, check_options, scheduled_check, reschedule_check, latency, start_time, finish_time, early_timeout, exited_ok, host_return_code, output_string):
	os.write(self.fh, "\n### Nagios Host Check Result ###\n")
        os.write(self.fh, "# Time: " + time.asctime() + "\n")
        os.write(self.fh, "host_name=" + host + "\n")
        os.write(self.fh, "check_type=" + str(check_type) + "\n")
        os.write(self.fh, "check_options=" + str(check_options) + "\n")
        os.write(self.fh, "scheduled_check=" + str(scheduled_check) + "\n")
        os.write(self.fh, "reschedule_check=" + str(reschedule_check) + "\n")
        os.write(self.fh, "latency=" + str(latency) + "\n")
        os.write(self.fh, "start_time=" + str(start_time) + "\n")
        os.write(self.fh, "finish_time=" + str(finish_time) + "\n")
        os.write(self.fh, "early_timeout=" + str(early_timeout) + "\n")
        os.write(self.fh, "exited_ok=" + str(exited_ok) + "\n")
        os.write(self.fh, "return_code=" + str(host_return_code) + "\n")
	if not output_string:
		os.write(self.fh, "output=" + " " + "Host (" + host + ")" + " " + self.host_state[host_return_code] + "\\n\n")
	else:
		os.write(self.fh, "output=" + " " + output_string + "\\n\n")
   
    # Accepts parameters required for the service checkresult
    # Writes service checks to the checkresult file 
    def build_service(self, host, service_name, check_type, check_options, scheduled_check, reschedule_check, latency, start_time, finish_time, early_timeout, exited_ok, service_return_code, metric_value, metric_units, output_string):
	os.write(self.fh, "\n### Nagios Service Check Result ###\n")
        os.write(self.fh, "# Time: " + time.asctime() + "\n")
        os.write(self.fh, "host_name=" + host + "\n")
        os.write(self.fh, "service_description=" + service_name + "\n")
        os.write(self.fh, "check_type=" + str(check_type) + "\n")
        os.write(self.fh, "check_options=" + str(check_options) + "\n")
        os.write(self.fh, "scheduled_check=" + str(scheduled_check) + "\n")
        os.write(self.fh, "reschedule_check=" + str(reschedule_check) + "\n")
        os.write(self.fh, "latency=" + str(latency) + "\n")
        os.write(self.fh, "start_time=" + str(start_time) + "\n")
        os.write(self.fh, "finish_time=" + str(finish_time) + "\n")
        os.write(self.fh, "early_timeout=" + str(early_timeout) + "\n")
        os.write(self.fh, "exited_ok=" + str(exited_ok) + "\n")
        os.write(self.fh, "return_code=" + str(service_return_code) + "\n")
	if not output_string:
        	os.write(self.fh, "output=" + service_name + " " + self.service_state[service_return_code] + "- " + service_name + " " +  str(metric_value) + " " + metric_units + "\\n\n")
	else:
		os.write(self.fh, "output=" + " " + output_string + "\\n\n")

    # Close the file handle and create an ok-to-go indicator file 
    def submit(self):
        os.close(self.fh)
        ok_filename = self.cmd_file + ".ok"
	print self.cmd_file
        ok_fh = file(ok_filename, 'a')
        ok_fh.close()

