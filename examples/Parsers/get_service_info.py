#!/usr/bin/python
import sys

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config


## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

service = nc.get_service("Users","wilmvpn")

print nc.print_conf(service)
