#!/usr/bin/python
from __future__ import absolute_import
from __future__ import print_function
import sys

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

def is_ip(ip_address):
    import socket
    try:
        socket.inet_aton(ip_address)
        return True # We got through that call without an error, so it is valid
    except socket.error:
        return False # There was an error, so it is invalid

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


print("Checking hosts using dns names instead of ip addresses in the 'address' field")
for host in nc['all_host']:
    if 'address' in host:
        if not is_ip(host['address']):
            print("%s has a name instead of ip in the address field (%s)" % (host['alias'], host['address']))


print("Checking for weird service definitions")
for service in nc['all_service']:
    if 'register' in service and service['register'] == 0:
        continue
    if 'host_name' not in service:
        print(nc.print_conf( service ))
