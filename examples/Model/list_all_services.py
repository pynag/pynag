#!/usr/bin/python

import sys
sys.path.insert(1, '/opt/pynag')
from pynag import Model


# If your nagios config is in an unusal place, uncomment this:
# Model.cfg_file = '/etc/nagios/nagios.cfg'

services = Model.Service.objects.all

print("%-30s  %-30s" % ("Hostname", "Service_description"))
for service in services:
    print("%-30s  %-30s" % ( service['host_name'], service['service_description'] ))
