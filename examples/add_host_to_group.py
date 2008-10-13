#!/usr/bin/python

#!/usr/bin/python
import os,sys

if len(sys.argv) != 3:
	sys.stderr.write("Usage:  %s 'Host Alias' group\n" % (sys.argv[0]))
	sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


target_host = sys.argv[1]
target_group = sys.argv[2]

print "Adding %s to %s" % (target_host, target_group)
nc.add_alias_to_hostgroup(target_host, target_group)

## Commit the changes to file
nc.commit()
