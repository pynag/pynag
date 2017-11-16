#!/usr/bin/python
import sys

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
print("The following hosts do not have parent items:")

for host in nc['all_host']:
    use_attr = ''
    for attribute in ['host_name', 'name', 'alias']:
        if attribute in host:
            use_attr = attribute
    
    if 'parents' not in host or not host['parents']:
        if  host[use_attr] not in top_level_items:
            orphan_hosts.append(host)
            print("%-12s %-32s (%s)" % (use_attr, host[use_attr], host['meta']['filename']))

if not len(orphan_hosts):
    print("No ophaned hosts found")
