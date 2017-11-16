#!/usr/bin/python

from __future__ import absolute_import
import os.path
import sys

pynagbase = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path[0] = pynagbase

# Standard init
from pynag.Plugins import PluginHelper, ok

# Create an instance of PluginHelper()
my_plugin = PluginHelper()

# Feed fake data for range checking
my_plugin.parser.add_option('-F', dest='fakedata', help='fake data to test thresholds')

# Activate
my_plugin.parse_arguments()

# Check if -F was provided
if my_plugin.options.fakedata is None:
    my_plugin.parser.error("Specify some value with -F")

my_plugin.add_status(ok)
my_plugin.add_summary(my_plugin.options.fakedata)
my_plugin.add_metric('fakedata', my_plugin.options.fakedata)

my_plugin.check_all_metrics()

my_plugin.exit()
