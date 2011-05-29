#!/usr/bin/python
import os,sys

if len(sys.argv) != 2:
	sys.stderr.write("Usage:  %s 'Timeperiod Name'\n" % (sys.argv[0]))
	sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_item = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


item = nc.get_timeperiod(target_item)

if not item:
	sys.stderr.write("Item not found: %s\n" % item)
	sys.exit(2)

print nc.print_conf(item)
