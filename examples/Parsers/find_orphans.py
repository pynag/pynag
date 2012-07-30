#!/usr/bin/python
import os,sys

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

## These are top level items.  We don't care if they dont' have a parent.
## Things like datacenters should be displayed here
top_level_items = ['main data center']



orphan_hosts = []
for host in nc['all_host']:
    if not host.has_key('parents'):
        if host['alias'] not in top_level_items:
            orphan_hosts.append(host)

if len(orphan_hosts) != 0:
    print "The following hosts do not have parent items:"
    for host in orphan_hosts:
        print "%s (%s)" % (host['alias'], host['meta']['filename'])
else:
    print "No ophaned hosts found"
