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
import re
import subprocess
import time
import getpass

from pynag import Parsers
import pynag.Control.Command
import pynag.Utils
from macros import _standard_macros

from all_attributes import AllAttributes
from string_to_class import StringToClass
from nagios_objects import *

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

def _add_object_to_group(my_object, my_group):
    """ Add one specific object to a specified objectgroup

    Examples:
    c = Contact()
    g = Contactgroup()

    _add_to_group(c, g )
    """
    # First of all, we behave a little differently depending on what type of an object we lets define some variables:
    group_type = my_group.object_type        # contactgroup,hostgroup,servicegroup
    group_name = my_group.get_shortname()    # admins
    object_name = my_object.get_shortname()  # root

    group_field = 'members'     # i.e. Contactgroup.members
    object_field = group_type + 's'  # i.e. Host.hostgroups

    groups = my_object[object_field] or ''  # f.e. value of Contact.contactgroups
    list_of_groups = pynag.Utils.AttributeList(groups)

    members = my_group[group_field] or ''     # f.e. Value of Contactgroup.members
    list_of_members = pynag.Utils.AttributeList(members)

    if group_name in list_of_groups:
        return False  # Group says it already has object as a member

    if object_name in list_of_members:
        return False  # Member says it is already part of group

    my_object.attribute_appendfield(object_field, group_name)
    my_object.save()
    return True


def _remove_object_from_group(my_object, my_group):
    """ Remove one specific object to a specified objectgroup

    Examples:
    c = Contact()
    g = Contactgroup()

    _remove_object_from_group(c, g )
    """
    # First of all, we behave a little differently depending on what type of an object we lets define some variables:
    group_type = my_group.object_type          # contactgroup,hostgroup,servicegroup
    group_name = my_group.get_shortname()      # admins
    object_name = my_object.get_shortname()  # root

    group_field = 'members'     # i.e. Contactgroup.members
    object_field = group_type + 's'  # i.e. Host.hostgroups

    groups = my_object[object_field] or ''  # e. value of Contact.contactgroups
    list_of_groups = pynag.Utils.AttributeList(groups)

    members = my_group[group_field] or ''     # f.e. Value of Contactgroup.members
    list_of_members = pynag.Utils.AttributeList(members)

    if group_name in list_of_groups:
        # Remove group from the object
        my_object.attribute_removefield(object_field, group_name)
        my_object.save()

    if object_name in list_of_members:
        # Remove object from the group
        my_group.attribute_removefield(group_field, object_name)
        my_group.save()


def _add_to_contactgroup(my_object, contactgroup):
    """ add Host or Service to a contactgroup
    """
    if isinstance(contactgroup, basestring):
        contactgroup = Contactgroup.objects.get_by_shortname(contactgroup)

    contactgroup_name = contactgroup.contactgroup_name

    if my_object.object_type == "contact":
        return _add_object_to_group(my_object, contactgroup)

    current_contactgroups = AttributeList(my_object.contact_groups)
    if contactgroup_name not in current_contactgroups.fields:
        my_object.attribute_appendfield('contact_groups', contactgroup_name)
        my_object.save()
        return True
    else:
        return False


def _remove_from_contactgroup(my_object, contactgroup):
    """ remove Host or Service from  a contactgroup
    """
    if isinstance(contactgroup, basestring):
        contactgroup = Contactgroup.objects.get_by_shortname(contactgroup)

    contactgroup_name = contactgroup.contactgroup_name
    if my_object.object_type == "contact":
        return _remove_object_from_group(my_object, contactgroup)

    current_contactgroups = AttributeList(my_object.contact_groups)
    if contactgroup_name in current_contactgroups.fields:
        my_object.attribute_removefield('contact_groups', contactgroup_name)
        my_object.save()
        return True
    else:
        return False


string_to_class = StringToClass(backend=backend)

# Attributelist is put here for backwards compatibility
AttributeList = pynag.Utils.AttributeList


def _add_property(ClassType, name):
    """ Create a dynamic property specific ClassType

    object_definition = ClassType()
    object_definition.name -> object_definition['name'

    So in human speak, this reads info from all_attributes and makes sure that
    Host has Host.host_name

    Returns: None
    """
    fget = lambda self: self[name]
    fset = lambda self, value: self.set_attribute(name, value)
    fdel = lambda self: self.set_attribute(name, None)
    fdoc = "This is the %s attribute for object definition"
    setattr(ClassType, name, property(fget, fset, fdel, fdoc))


# Add register, name and use to all objects
_add_property(ObjectDefinition, 'register')
_add_property(ObjectDefinition, 'name')
_add_property(ObjectDefinition, 'use')

all_attributes = AllAttributes(backend=backend)
# For others, create attributes dynamically based on all_attributes.keys()
for object_type, attributes in all_attributes.object_definitions.items():
    # Lets find common attributes that every object definition should have:
    if object_type == 'any':
        continue
    if string_to_class.get(object_type) == None:
        continue
    Object = string_to_class.get(object_type)

    for attribute in attributes:
        _add_property(Object, attribute)

if __name__ == '__main__':
    pass
