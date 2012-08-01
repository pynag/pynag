#!/usr/bin/python
import sys

if len(sys.argv) != 2:
    sys.stderr.write("Usage:  %s 'Host Alias'\n" % (sys.argv[0]))
    sys.exit(2)

## This is for the custom nagios module
sys.path.insert(1, '../')
from pynag.Parsers import config

target_host = sys.argv[1]

## Create the plugin option
nc = config('/etc/nagios/nagios.cfg')
nc.extended_parse()

nc.cleanup()

## Find services that this host belongs to
if not nc.get_host(target_host):
    sys.stderr.write("%s does not exist\n" % target_host)
    sys.exit(2)


for service_description in nc.get_host(target_host)['meta']['service_list']:
    service = nc.get_service(target_host, service_description)

    ## Check to see if this is the only host in this service
    host_list = []
    if service.has_key('host_name'):
        for host in nc._get_list(service, 'host_name'):
            if host[0] != "!":
                host_list.append(host)
    else:
        continue

    ## Ignore if this host isn't listed
    if len(host_list) == 0:
        continue


    if len(host_list) > 1:
        print "Removing %s from %s" % (target_host, service['service_description'])
        new_item = nc.get_service(service['service_description'], target_host)
        host_list.remove(target_host)
        host_string = ",".join(host_list)
        print "New Value: %s" % host_string
        nc.edit_service(target_host, service['service_description'], 'host_name',host_string)
    elif (len(host_list) == 1) and not service.has_key('hostgroup_name'):
        print "Deleting %s" % service['service_description']
        nc.delete_service(service['service_description'], target_host)
    elif (len(host_list) == 1) and (host_list[0] is target_host):
        print "Deleting %s" % service['service_description']
        nc.delete_service(service['service_description'], target_host)
    else:
        print "Unknown Action"
        sys.exit(2)
    nc.commit()

## Delete from groups
host_obj = nc.get_host(target_host)
for hostgroup in host_obj['meta']['hostgroup_list']:
    print "Removing %s from hostgroup %s" % (target_host, hostgroup)
    hostgroup_obj = nc.get_hostgroup(hostgroup)

    ## Get the list
    #hostgroup_obj['members'] = nc._get_list(hostgroup_obj, 'members').remove(target_host)

    ## Remove the original objct
    member_list = nc._get_list(hostgroup_obj, 'members')
    member_list.remove(target_host)

    nc['all_hostgroup'].remove(hostgroup_obj)
    hostgroup_obj['meta']['needs_commit'] = True
    member_string = ",".join(member_list)
    hostgroup_obj['members'] = ",".join(member_list)
    nc['all_hostgroup'].append(hostgroup_obj)
    
    nc.commit()

## Delete a host
result = nc.delete_object('host',target_host)
if result:
    print "Deleted host"

## Delete hostextinfo
result = nc.delete_object('hostextinfo',target_host)
if result:
    print "Deleted hostextinfo"

nc.commit()
nc.cleanup()
