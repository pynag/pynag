#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
import sys
sys.path.insert(1, '/opt/pynag')
from pynag import Model


# If your nagios config is in an unusal place, uncomment this:
# Model.cfg_file = '/etc/nagios/nagios.cfg'


# Lets find all services that belong to the host "localhost"
host_name = "localhost"

services = Model.Service.objects.filter(host_name='localhost')

print("%-30s  %-30s" % ("Hostname", "Service_description"))
for service in services:
    print("%-30s  %-30s" % ( service['host_name'], service['service_description'] ))
