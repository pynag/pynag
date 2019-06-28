#!/usr/bin/python
from __future__ import absolute_import
import os,sys

## Import plugin from nagios Module
from pynag.Plugins import simple as Plugin


## Create the plugin option
np = Plugin()

## Add a command line argument
np.add_arg("l","load-file", "Enter a load average file", required=None)

## This starts the actual plugin activation
np.activate()

## Use a custom load average file, if specified to
if np['load-file']:
    load_file = np['load-file']
else:
    load_file = "/proc/loadavg"

if not os.path.isfile(load_file):
    np.nagios_exit("UNKNOWN", "Missing Load average file %s" % load_file)

## Get the check value
current_load = open(load_file).readline().split()[0]

## Add the perdata
np.add_perfdata("1min", current_load)

np.check_range(current_load)
