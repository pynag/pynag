#!/usr/bin/python

from __future__ import absolute_import
import os.path
import sys

pynagbase = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path[0] = pynagbase

# Standard init
import pynag.Plugins
from pynag.Plugins import WARNING, CRITICAL, OK, UNKNOWN, simple as Plugin

np = Plugin(must_threshold=False)

# Feed fake data for range checking
np.add_arg('F', 'fakedata', 'fake data to test thresholds', required=True)

# Activate
np.activate()

# Test supplied fake data against thresholds
np.check_range(int(np['fakedata']))
