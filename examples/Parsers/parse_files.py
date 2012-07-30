#!/usr/bin/python
import os,sys

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()
#nc._post_parse()
for host in nc['all_host']:
    print nc.print_conf(host)
