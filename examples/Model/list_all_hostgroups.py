#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
import sys
sys.path.insert(1, '/opt/pynag')
from pynag import Model


# If your nagios config is in an unusal place, uncomment this:
# Model.cfg_file = '/etc/nagios/nagios.cfg'

hostgroups = Model.Hostgroup.objects.all

for hostgroup in hostgroups:
    print(hostgroup['hostgroup_name'])

