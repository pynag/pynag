#!/usr/bin/python
import sys

if len(sys.argv) != 3:
    sys.stderr.write("Usage:  %s 'Host Name' 'Service Description'\n" % (sys.argv[0]))
    sys.exit(2)


## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config


## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

service = nc.get_service(sys.argv[1],sys.argv[2])

print nc.print_conf(service)
