#!/usr/bin/python
import os,sys

if len(sys.argv) != 2:
	sys.stderr.write("Usage:  %s 'Host Alias'\n" % (sys.argv[0]))
	sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_host = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

nc.delete_object('host',target_host)
nc.commit()
nc.delete_object('hostextinfo',target_host)
nc.commit()
