#!/usr/bin/python

#!/usr/bin/python
import os,sys

if len(sys.argv) != 3:
	sys.stderr.write("Usage:  %s 'Host Name' 'Hostgroup Name' \n" % (sys.argv[0]))
	sys.exit(2)

## This is for the custom nagios module
from pynag.Parsers import config

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.parse()


target_host = sys.argv[1]
target_group = sys.argv[2]


## Get the host object
host_obj = nc.get_host(target_host)
if not host_obj:
	sys.stderr.write("host_name '%s' does not exist\n" % target_host)
	sys.exit(2)

## Find the hostgroup from our global dictionaries
group_obj = nc.get_hostgroup(target_group)
if not group_obj:
	sys.stderr.write("%s does not exist\n" % target_group)
	sys.exit(2)

## Get a list of the host_name's in this group
existing_list = group_obj['members'].split(",")
if target_host in existing_list:
	sys.stderr.write("%s is already in the group\n" % target_host)
	sys.exit(2)
else:
	existing_list.append(target_host)

print "Adding %s to %s" % (target_host, target_group)

## Alphabetize the list, for easier readability (and to make it pretty)
existing_list.sort()

## Remove old group
nc['all_hostgroup'].remove(group_obj)

## Save the new member list
group_obj['members'] = ",".join(existing_list)

## Mark the commit flag for the group
group_obj['meta']['needs_commit'] = True

## Add the group back in with new members
nc['all_hostgroup'].append(group_obj)


## Commit the changes to file
nc.commit()
