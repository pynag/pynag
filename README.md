ABOUT
=====
Pynag a tool and a library for managing nagios configuration and provides a
framework to write plugins.

Pynag command-line utility offers the following features:
  - Command-line tool to view/edit configuration
  
The pynag modules offer the following features:
  - Parse, view and edit configuration
  - Framework for writing your own nagios plugins
  - stop/start/reload nagios service


INSTALL
=======
Using fedora/redhat:

    yum install pynag

Using debian/ubuntu:

    apt-get install python-pynag

Install latest git repository from source:

    git clone https://github.com/pynag/pynag.git
    cd pynag
    python setup.py build
    python setup.py instal

Getting started
===============
List all services:

    import pynag.Model
    all_services pynag.Model.Service.objects.all
    for i in all_services:
    print i.host_name, i.service_description

Change an address of a host:

    import pynag.Model
    myhost = pynag.Model.Host.objects.get_by_shortname('myhost.example.com')
    myhost.address = '127.0.0.1'
    myhost.save()
    # See what the host definition looks like after change:
    print myhost

Create a new ssh service check for every host in the unix hostgroup:

    import pynag.Model
    hosts = pynag.Model.Host.objects.filter(hostgroup="unixservers")
    for host in hosts:
        new_service = pynag.Model.Service()
        new_service.host_name = host.host_name
        new_service.service_description = "SSH Connectivity"
        new_service.check_command = "check_ssh"
        # optionally control where new object is saved:
        new_service.set_filename( host.get_filename() )
        new_service.save()

PYNAG COMMAND-LINE TOOL
=======================
Pynag also comes with a command-line tool that gives good examples what is
possible with the library. Some example commands:

list all hosts and their ip address:

    pynag list host_name address where object_type=host

Change contactgroup for all services for a particular host:

    pynag update set contactgroups=admins where host_name="myhost" and object_type=service

Copy a host, give it a new hostname and ip address:

    pynag copy set host_name=newhost address=newaddress where object_type=host and host_name=oldhost
    # Same for all its services:
    pynag copy set host_name=newhost where object_type=service and host_name=oldhost

KNOWN ISSUES
============
Model module's get_effective_* functions are not complete if your configuration is using regular expressions. For example, pynag.Model.Service.get_effective_hosts will fail on the following service definition:

    define service {
        service_description check http
        check_command check_http
        host_name www*
    } 

Same applies for exemptions like this one:

    define service {
        service_description check http
        check_command check_http
        hostgroup_name webservers
	host_name !dmzhost1,dmzhost2
    }
