#!/usr/bin/python
#
# Example script on how to modify a single Nagios service

from pynag import Model
import sys

# Parse commandline arguments
if len(sys.argv) != 5:
	print '''
Usage:
  %s <host_name> <service_description> <field_name> <new_value>

Example:
  %s localhost Ping check_command 'check_ping'
''' % (sys.argv[0], sys.argv[0])
	sys.exit(1)

host_name = sys.argv[1]
service_description = sys.argv[2]
field_name = sys.argv[3]
new_value = sys.argv[4]


# Get a list of all services that fit our search pattern
search_results = Model.Service.objects.filter(host_name=host_name, service_description=service_description)

if len(search_results) == 0:
	print "no service found for host_name=%s and service_description=%s" % ( host_name, service_description )

my_service = search_results[0]
my_service.set_attribute(field_name,new_value)
my_service.save()


