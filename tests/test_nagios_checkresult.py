#! /usr/bin/python

import unittest
import time
import textwrap
import nagios_checkresult

class TestNagiosCheckResult(unittest.TestCase):
    def setUp (self):
	self.maxDiff = None
	#this is how checkresult file should look like
	self.checkresult = textwrap.dedent("""\
	### Active Check Result File ###
	file_time=1400347643.73

	### Nagios Host Check Result ###
	# Time: Sat May 17 22:57:23 2014
	host_name=xyz
	check_type=0
	check_options=0
	scheduled_check=1
	reschedule_check=1
	latency=0.1
	start_time=1399732963.0
	finish_time=1399732963.0
	early_timeout=0
	exited_ok=1
	return_code=0
	output= Host (xyz) UP\\n

	### Nagios Service Check Result ###
	# Time: Sat May 17 22:57:23 2014
	host_name=xyz
	service_description=Total processes
	check_type=0
	check_options=0
	scheduled_check=1
	reschedule_check=1
	latency=0.1
	start_time=1399732963.0
	finish_time=1399732963.0
	early_timeout=0
	exited_ok=1
	return_code=0
	output=Total processes OK- Total processes 288 \\n\n""")
	
    def test_checkresult(self):
	#generate checkresult file by sending data to GenerateNagiosCheckResult 
	ng = nagios_checkresult.GenerateNagiosCheckResult()	
	ng.create('/var/lib/nagios3/spool/checkresults', 1400347643.73)
	ng.build_host('Sat May 17 22:57:23 2014', 'xyz', 0, 0, 1, 1, 0.1, str(1399732963.0), str(1399732963.0), 0, 1, 0, "")
	ng.build_service('Sat May 17 22:57:23 2014', 'xyz', 'Total processes', 0, 0, 1, 1, 0.1, str(1399732963.0), str(1399732963.0), 0, 1, 0, 288, "", "")
	#fname is the name of checkresult file generated
	fname = ng.submit()
	self.testfile = open(fname).read()
	#compare the expected checkresult file with generated checkresult file
	self.assertMultiLineEqual(self.testfile, self.checkresult, msg=None)

if __name__ == '__main__':
    unittest.main()
