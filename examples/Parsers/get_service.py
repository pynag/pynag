#!/usr/bin/python
import sys

if len(sys.argv) != 3:
    sys.stderr.write("Usage:  %s 'Service Description' 'Host Name'\n" % (sys.argv[0]))
    sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

service_description = sys.argv[1]
target_host = sys.argv[2]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
#nc.parse()
nc.parse()

service = nc.get_service(target_host, service_description)

if not service:
    sys.stderr.write("Service not found: %s %s\n" % (service_description, target_host))
    sys.exit(2)

print(nc.print_conf(service))

