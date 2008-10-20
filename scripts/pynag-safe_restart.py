#!/usr/bin/python
import os,sys

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Control import daemon

## Create the plugin option
nd = daemon()

if not nd.verify_config():
	sys.stderr.write("Bad configuration, exiting\n")
	sys.exit(2)

nd.restart()
