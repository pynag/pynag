#!/usr/bin/python
#
# This example shows how to work with attributes in nagios that
# Are in a comma-seperated form. Like this:
#
# define service {
#    contact_groups      +admins,webmasters,hostmasters
#    host_name           host.example.com
#    service_description Test Service
# }
#

import pynag.Model

# First create a test object
my_service = pynag.Model.Service()
my_service['host_name'] = 'examplehost'
my_service['service_description'] = 'Test Service'
my_service['contact_groups'] = '+admins,webmasters,hostmasters'

print "*** Created a demo servicecheck that looks like this:"
print my_service



print "\n--- Removing with attribute_removefield()"
my_service.attribute_removefield('contact_groups', 'hostmasters')
print "my_service.contact_groups = ", my_service.contact_groups



print "\n--- Add a new contact_group with attribute_appendfield()"
my_service.attribute_appendfield('contact_groups', "mycontactgroup")
print "my_service.contact_groups = ", my_service.contact_groups

print "\n-- Replacing a contact_group midfield with attribute_replacefield()"
my_service.attribute_replacefield('contact_groups', "webmasters", "hostmaster")
print "my_service.contact_groups = ", my_service.contact_groups


# A more advanced example. Find all services that inherit from "generic-service" and
# Replace it with "my-specific-service":

print "\n--- More advanced example, editing multiple objects at once..."
my_services = pynag.Model.Service.objects.filter(use__hasfield='generic-service')

for service in my_services:
    service.attribute_replacefield('use','generic-service','my-specific-service')
    # service.save()


