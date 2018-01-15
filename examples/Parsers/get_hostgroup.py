#!/usr/bin/python
from __future__ import absolute_import
from __future__ import print_function
import sys

if len(sys.argv) != 2:
    sys.stderr.write("Usage:  %s 'Hostgroup'\n" % (sys.argv[0]))
    sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_host = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


hostgroup = nc.get_hostgroup(target_host)

if not hostgroup:
    sys.stderr.write("Hostgroup not found: %s\n" % hostgroup)
    sys.exit(2)

print(nc.print_conf(hostgroup))

