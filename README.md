[![Build Status](https://travis-ci.org/pynag/pynag.png?branch=master)](https://travis-ci.org/pynag/pynag)
[![Coverage Status](https://coveralls.io/repos/pynag/pynag/badge.png?branch=master)](https://coveralls.io/r/pynag/pynag?branch=master)
[![PyPI version](https://badge.fury.io/py/pynag.png)](http://badge.fury.io/py/pynag)


About
=====
Pynag a tool and a library for managing nagios configuration and provides a
framework to write plugins.

Pynag command-line utility offers the following features:
  - list python object definitions (e.g. list all hosts/services)
  - create new object definitions from command line
  - copy object definitions
  - remove object definitions
  - edit nagios.cfg from command-line
  
Pynag also has the following modules:
  - Model   - Easy way to work with configuration as python objects
  - Plugins - convenience classes for writing python plugins
  - Parsers - Various parsers for nagios configuration files
  - Control - Control of Nagios daemon


Install
=======
Using fedora/redhat:

    yum install pynag

Using debian/ubuntu:

    apt-get install python-pynag pynag

Using pip:

    pip install pynag

Install latest git repository from source:

    git clone https://github.com/pynag/pynag.git
    cd pynag
    python setup.py build
    python setup.py install

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

Further Documentation
=====================

We blatantly admit that documentation is scarce in pynag. Most of the documentation
is in-line in pydoc strings in the respective python modules.

Any help with improving the documentation is much appreciated. For more documentation see
* The pynag/examples directory
* Our github wiki: https://github.com/pynag/pynag/wiki

Pynag Command Line Tool
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

Known Issues
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


Who uses pynag
==============

There are a few open source projects out there that use pynag. The ones we
know of are:

* Adagios: Impressive web configuration and status interface
* Okconfig: Monitoring pack generator for Nagios
* RESTlos: generic RESTful api for nagios-like monitoring systems

Pynag is also used by lots of plugins around the world including:

* check_eva.py
* check_hpacucly.py
* check_ipa/check_ipa_replication


Know of more projects using pynag ? Contact us and we'll add them here.

Contact us
==========

If you need any help, want to contribute or just want to talk about pynag you can find us on one of the following:

* Bug reports, feature requests: https://github.com/pynag/pynag/issues
* Mailing list: https://groups.google.com/forum/?fromgroups#!forum/pynag-discuss
* Irc chat: #pynag on freenode

