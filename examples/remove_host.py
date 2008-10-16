#!/usr/bin/python
import os,sys

if len(sys.argv) != 2:
	sys.stderr.write("Usage:  %s 'Host Alias'\n" % (sys.argv[0]))
	sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_host = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()

## Find services that this host belongs to
for service in nc.get_service_membership(target_host):

	## Check to see if this is the only host in this service
	if service.has_key('host_name'):
		if service['host_name'].find(",") == -1:
			host_list = [service['host_name']]
		else:
			host_list = service['host_name'].split(",")
	else:
		continue

	#host_list = nc.get_service_members(service['name'])
	if len(host_list) > 1:
		print "Removing %s from %s" % (target_host, service)
		new_item = nc.get_object('service',service)
		host_list.remove(target_host)
		host_string = ",".join(host_list)
		print "New Value: %s" % host_string
		nc.edit_object('service',service, 'host_name',host_string)
	elif (len(host_list) == 1) and not service.has_key('hostgroup_name'):
		print "Deleting %s" % service['name']
		nc.delete_object('service', service['name'])
	elif (len(host_list) == 1) and (host_list[0] is target_host):
		print "Deleting %s" % service['name']
		nc.delete_object('service', service['name'])
	else:
		print "Unknown Action"
		sys.exit(2)

## Delete from groups
for hostgroup in nc.get_hostgroup_membership(target_host):
	print "Removing %s from %s" % (target_host, hostgroup)
	nc.remove_name_from_hostgroup(target_host, hostgroup)
	nc.commit()

## Delete a host
result = nc.delete_object('host',target_host)
if result:
	print "Deleted host"

## Delete hostextinfo
result = nc.delete_object('hostextinfo',target_host)
if result:
	print "Deleted hostextinfo"
