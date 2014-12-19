# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2011 Pall Sigurdsson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
This module provides a high level Object-Oriented wrapper
around pynag.Parsers.config.

Example:

>>> from pynag.Model import Service, Host
>>>
>>> all_services = Service.objects.all
>>> my_service = all_services[0]
>>> print my_service.host_name # doctest: +SKIP
localhost
>>>
>>> example_host = Host.objects.filter(host_name="host.example.com")
>>> canadian_hosts = Host.objects.filter(host_name__endswith=".ca")
>>>
>>> for i in canadian_hosts:
...     i.alias = "this host is located in Canada"
...     i.save() # doctest: +SKIP
"""

import os
import subprocess
import time
import getpass

from pynag import Parsers
import pynag.Control.Command
import pynag.Utils
from macros import _standard_macros

# from all_attributes import AllAttributes
from string_to_class import StringToClass
from object_factory import ObjectFactory

# Path To Nagios configuration file
cfg_file = None  # '/etc/nagios/nagios.cfg'

# Were new objects are written by default
pynag_directory = None

# This is the config parser that we use internally, if cfg_file is changed, then config
# will be recreated whenever a parse is called.
config = Parsers.config(cfg_file=cfg_file)

#: eventhandlers -- A list of Model.EventHandlers object.
# Event handler is responsible for passing notification whenever something
# important happens in the model.
#
# For example FileLogger class is an event handler responsible for logging to
# file whenever something has been written.
eventhandlers = []

# DEBUG FORCE SET BACKEND
backend = 'nagios'
string_to_class = StringToClass(backend=backend)
factory = ObjectFactory(backend=backend)
factory.prepare_object_module(config, eventhandlers, pynag_directory)

# Attributelist is put here for backwards compatibility
# AttributeList = pynag.Utils.AttributeList

# all_attributes = AllAttributes(backend=backend)
Contact = factory.Contact
Service = factory.Service
Host = factory.Host
Hostgroup = factory.Hostgroup
Contactgroup = factory.Contactgroup
Servicegroup = factory.Servicegroup
Timeperiod = factory.Timeperiod
HostDependency = factory.HostDependency
ServiceDependency = factory.ServiceDependency
HostEscalation = factory.HostEscalation
ServiceEscalation = factory.ServiceEscalation
Command = factory.Command
ObjectDefinition = factory.ObjectDefinition
ObjectRelations = factory.ObjectRelations

if __name__ == '__main__':
    pass
