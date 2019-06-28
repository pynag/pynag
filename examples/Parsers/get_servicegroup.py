#!/usr/bin/python
from __future__ import absolute_import
from __future__ import print_function
import sys

if len(sys.argv) != 2:
    sys.stderr.write("Usage:  %s 'Servicegroup Name'\n" % (sys.argv[0]))
    sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_servicegroup = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


item = nc.get_servicegroup(target_servicegroup)

if not item:
    sys.stderr.write("Item not found: %s\n" % item)
    sys.exit(2)

print(nc.print_conf(item))
