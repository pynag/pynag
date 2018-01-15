#!/usr/bin/python
from __future__ import absolute_import
from __future__ import print_function
import sys

if len(sys.argv) != 2:
    sys.stderr.write("Usage:  %s 'Host Alias'\n" % (sys.argv[0]))
    sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_host = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
#nc.parse()
nc.extended_parse()

## Find services that this host belongs to
for service in nc.get_host(target_host)['meta']['service_list']:
    ## Check to see if this is the only host in this service
    #return_item = nc.get_service(target_host, service_description)
    print(service)
#    print return_item['service_description']
