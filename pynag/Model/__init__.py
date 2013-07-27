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

example usage:

from pynag.Parsers import Service,Host

all_services = Service.objects.all
my_service=all_service[0]
print my_service.host_name

example_host = Host.objects.filter(host_name="host.example.com")
canadian_hosts = Host.objects.filter(host_name__endswith=".ca")

for i in canadian_hosts:
    i.alias = "this host is located in Canada"
    i.save()
"""

import os
import re
import subprocess
import time
import getpass

from pynag import Parsers
from pynag import Control
import pynag.Control.Command
import pynag.Utils
from macros import _standard_macros
import all_attributes


# Path To Nagios configuration file
cfg_file = None  # '/etc/nagios/nagios.cfg'

# Were new objects are written by default
pynag_directory = None

# This will be a Parsers.config instance once we have parsed
config = None
#config.parse()


#: eventhandlers -- A list of Model.EventHandlers object.
# Event handler is responsible for passing notification whenever something
# important happens in the model.
#
# For example FileLogger class is an event handler responsible for logging to
# file whenever something has been written.
eventhandlers = []

try:
    from collections import defaultdict
except ImportError:
    from pynag.Utils import defaultdict


def debug(text):
    if debug == True:
        print text


def contains(str1, str2):
    """Returns True if str1 contains str2"""
    if not str1:
        return False
    if str1.find(str2) > -1:
        return True


def not_contains(str1, str2):
    """Returns True if str1 does not contain str2"""
    return not contains(str1, str2)


def has_field(str1, str2):
    """Returns True if str2 is a field in str1

    For this purpose the string 'example' is a field in '+this,is,an,example'
    """
    str1 = str1.strip('+')
    str1 = str1.split(',')
    str1 = map(lambda x: x.strip(), str1)
    if str2 in str1:
        return True
    return False


class ObjectRelations(object):
    """ Static container for objects and their respective neighbours """
    # c['contact_name'] = [host1.get_id(),host2.get_id()]
    contact_hosts = defaultdict(set)

    # c['contact_name'] = ['contactgroup1','contactgroup2']
    contact_contactgroups = defaultdict(set)

    # c['contact_name'] = ['service1.get_id()','service2.get_id()']
    contact_services = defaultdict(set)

    # c['contactgroup_name'] = ['contact1.contact_name','contact2.contact_name','contact3.contact_name']
    contactgroup_contacts = defaultdict(set)

    # c['contactgroup_name'] = ['contactgroup1','contactgroup2','contactgroup3']
    contactgroup_contactgroups = defaultdict(set)

    # c['contactgroup_name'] = ['host1.get_id()', 'host2.get_id()']
    contactgroup_hosts = defaultdict(set)

    # c['contactgroup_name'] = ['service1.get_id()', 'service2.get_id()']
    contactgroup_services = defaultdict(set)

    # c['host_name'] = [service1.id, service2.id,service3.id]
    host_services = defaultdict(set)

    # c['host_name'] = ['contactgroup1', 'contactgroup2']
    host_contact_groups = defaultdict(set)

    # c['host_name'] = ['contact1','contact2']
    host_contacts = defaultdict(set)

    # c['host_name'] = '['hostgroup1.hostgroup_name','hostgroup2.hostgroup_name']
    host_hostgroups = defaultdict(set)

    # c['host_name'] = '['service1.get_id()','service2.get_id()']
    host_services = defaultdict(set)

    # c['hostgroup_name'] = ['host_name1','host_name2']
    hostgroup_hosts = defaultdict(set)

    # c['hostgroup_name'] = ['hostgroup1','hostgroup2']
    hostgroup_hostgroups = defaultdict(set)

    # c['hostgroup_name'] = ['service1.get_id()','service2.get_id()']
    hostgroup_services = defaultdict(set)

    # c['service.get_id()'] = '['contactgroup_name1','contactgroup_name2']
    service_contact_groups = defaultdict(set)

    # c['service.get_id()'] = '['contact_name1','contact_name2']
    service_contacts = defaultdict(set)

    # c['service.get_id()'] = '['hostgroup_name1','hostgroup_name2']
    service_hostgroups = defaultdict(set)

    # c['service.get_id()'] = '['servicegroup_name1','servicegroup_name2']
    service_servicegroups = defaultdict(set)

    # c['service.get_id()'] = ['host_name1','host_name2']
    service_hosts = defaultdict(set)

    # c['servicegroup_name'] = ['service1.get_id()', ['service2.get_id()']
    servicegroup_services = defaultdict(set)

    # c['servicegroup_name'] = ['servicegroup1','servicegroup2','servicegroup3']
    servicegroup_servicegroups = defaultdict(set)

    # c[command_name] = '['service.get_id()','service.get_id()']
    command_service = defaultdict(set)

    # c[command_name] = '['host_name1','host_name2']
    command_host = defaultdict(set)

    # use['host']['host_name1'] = ['host_name2','host_name3']
    # use['contact']['contact_name1'] = ['contact_name2','contact_name3']
    _defaultdict_set = lambda: defaultdict(set)
    use = defaultdict(_defaultdict_set)

    # contactgroup_subgroups['contactgroup_name'] = ['group1_name','group2_name']
    contactgroup_subgroups = defaultdict(set)

    # hostgroup_subgroups['hostgroup_name'] = ['group1_name','group2_name']
    hostgroup_subgroups = defaultdict(set)

    # servicegroup_subgroups['servicegroup_name'] = ['servicegroup1_name','servicegroup2_name']
    servicegroup_subgroups = defaultdict(set)

    # servicegroup_members['servicegroup_name'] = ['service1_shortname','service2_shortname']
    servicegroup_members = defaultdict(set)

    @staticmethod
    def reset():
        """ Runs clear() on every member attribute in ObjectRelations """
        for k, v in ObjectRelations.__dict__.items():
            if isinstance(v, defaultdict):
                v.clear()

    @staticmethod
    def _get_subgroups(group_name, dictname):
        """ Helper function that lets you get all sub-group members of a particular group

        For example this call:
          _get_all_group-members('admins', ObjectRelations.contactgroup_contacgroups)

        Will return recursively go through contactgroup_members of 'admins' and return a list
        of  all subgroups
        """
        subgroups = dictname[group_name].copy()
        checked_groups = set()
        while len(subgroups) > 0:
            i = subgroups.pop()
            if i not in checked_groups:
                checked_groups.add(i)
                subgroups.update(dictname[i])
        return checked_groups

    @staticmethod
    def resolve_regex():
        """ If any object relations are a regular expression, then expand them into a full list """
        self = ObjectRelations
        expand = self._expand_regex
        shortnames = ObjectFetcher._cached_shortnames

        host_names = shortnames['host'].keys()
        hostgroup_names = shortnames['hostgroup'].keys()
        servicegroup_names = shortnames['servicegroup'].keys()
        contact_names = shortnames['contact'].keys()
        contactgroup_names = shortnames['contactgroup'].keys()
        service_names = shortnames['service'].keys()  # Will be a host/service_description string

        expand(self.hostgroup_hosts, host_names)
        expand(self.host_hostgroups, hostgroup_names)
        expand(self.service_hostgroups, hostgroup_names)
        #expand(self.service_hosts, host_names)
        #expand(self.service_hosts, host_names)

    @staticmethod
    def _expand_regex(dictionary, full_list):
        """ Replaces any regex found in dictionary.values() or dictionary.keys() **INPLACE** with its respective matches found in full_list

        Example with ObjectRelations.hostgroup_hosts
        >>> hostnames = set(['localhost','remotehost', 'not_included'])
        >>> hostgroup_hosts = {'hostgroup1': set([ '.*host' ]), 'hostgroup2' : set(['localhost','remotehost']), }
        >>> ObjectRelations._expand_regex(dictionary=hostgroup_hosts, full_list=hostnames)
        >>> hostgroup_hosts['hostgroup1'] == hostgroup_hosts['hostgroup2']
        True
        >>> hostgroup_hosts['hostgroup1'] == set(['localhost','remotehost'])
        True
        """
        if config.get_cfg_value('use_true_regexp_matching') == "1":
            always_use_regex = True
        else:
            always_use_regex = False
        is_regex = lambda x: x is not None and (always_use_regex or '*' in x or '?' in x or '+' in x or '\.' in x)

        # Strip None entries from full_list
        full_list = filter(lambda x: x is not None, full_list)

        # Strip None entries from dictionary

        # If any keys in the dictionary are regex, expand it, i.e.:
        # if dictionary = { '.*':[1], 'localhost':[],'remotehost':[] }
        # then do:
        # dictionary['localhost'].update( [1] )
        # dictionary['remotehost'].update( [1] )
        # del dictionary['.*']
        regex_keys = filter(is_regex, dictionary.keys())
        for key in regex_keys:
            regex = re.compile(key)
            expanded_list = filter(regex.search, regex_keys)
            for i in expanded_list:
                if i == key:  # No need to react if regex resolved to itself
                    continue
                dictionary[i].update(dictionary[key])
            if key not in expanded_list:
                # Only remove the regex if it did not resolve to itself.
                del dictionary[key]
            # If dictionary.values() has any regex, expand it like so:
        # full_list = [1,2,3]
        # if dictionary = {'localhost':[ '.*' ]}
        # then change it so that:
        # dictionary = { 'localhost':[1,2,3] }
        for key, value in dictionary.items():
            regex_members = filter(is_regex, value)
            if len(regex_members) == 0:
                continue  # no changes need to be made
            if isinstance(value, list):
                value = set(value)
                #new_value = value.copy()
            for i in regex_members:
                regex = re.compile(i)
                expanded_list = filter(regex.search, full_list)
                value.remove(i)
                value.update(expanded_list)
                #dictionary[key] = new_value

    @staticmethod
    def resolve_contactgroups():
        """ Update all contactgroup relations to take into account contactgroup.contactgroup_members """
        groups = ObjectRelations.contactgroup_contactgroups.keys()
        for group in groups:
            subgroups = ObjectRelations._get_subgroups(group, ObjectRelations.contactgroup_contactgroups)
            ObjectRelations.contactgroup_subgroups[group] = subgroups

            # Loop through every subgroup and apply its attributes to ours
            for subgroup in subgroups:
                for i in ObjectRelations.contactgroup_contacts[subgroup]:
                    ObjectRelations.contact_contactgroups[i].add(group)
                for i in ObjectRelations.contactgroup_hosts[subgroup]:
                    ObjectRelations.host_contact_groups[i].add(group)
                for i in ObjectRelations.contactgroup_services[subgroup]:
                    ObjectRelations.service_contact_groups[i].add(group)
                ObjectRelations.contactgroup_contacts[group].update(ObjectRelations.contactgroup_contacts[subgroup])
                ObjectRelations.contactgroup_hosts[group].update(ObjectRelations.contactgroup_hosts[subgroup])
                ObjectRelations.contactgroup_services[group].update(ObjectRelations.contactgroup_services[subgroup])

    @staticmethod
    def resolve_hostgroups():
        """ Update all hostgroup relations to take into account hostgroup.hostgroup_members """
        groups = ObjectRelations.hostgroup_hostgroups.keys()
        for group in groups:
            subgroups = ObjectRelations._get_subgroups(group, ObjectRelations.hostgroup_hostgroups)
            ObjectRelations.hostgroup_subgroups[group] = subgroups

            # Loop through every subgroup and apply its attributes to ours
            for subgroup in subgroups:
                for i in ObjectRelations.hostgroup_hosts[subgroup]:
                    ObjectRelations.host_hostgroups[i].add(group)
                for i in ObjectRelations.hostgroup_services[subgroup]:
                    ObjectRelations.service_hostgroups[i].add(group)
                ObjectRelations.hostgroup_hosts[group].update(ObjectRelations.hostgroup_hosts[subgroup])
                ObjectRelations.hostgroup_services[group].update(ObjectRelations.hostgroup_services[subgroup])

    @staticmethod
    def resolve_servicegroups():
        """ Update all servicegroup relations to take into account servicegroup.servicegroup_members """

        # Before we do anything, resolve servicegroup.members into actual services
        ObjectRelations._resolve_servicegroup_members()

        groups = ObjectRelations.servicegroup_servicegroups.keys()
        for group in groups:
            subgroups = ObjectRelations._get_subgroups(group, ObjectRelations.servicegroup_servicegroups)
            ObjectRelations.servicegroup_subgroups[group] = subgroups

            # Loop through every subgroup and apply its attributes to ours
            for subgroup in subgroups:
                for i in ObjectRelations.servicegroup_services[subgroup]:
                    ObjectRelations.service_servicegroups[i].add(group)
                ObjectRelations.servicegroup_services[group].update(ObjectRelations.servicegroup_services[subgroup])

    @staticmethod
    def _resolve_servicegroup_members():
        """ Iterates through all servicegroup.members, and updates servicegroup_services and service_servicegroups.

            This happens post-parse (instead of inside Servicegroup._do_relations() because when parsing Servicegroup
            you only know host_name/service_description of the service that belongs to the group.

            However the relations we update work on Service.get_id() because not all services that belong to servicegroups
            have a valid host_name/service_description pair (templates)
        """
        for servicegroup, members in ObjectRelations.servicegroup_members.items():
            for shortname in members:
                try:
                    service = Service.objects.get_by_shortname(shortname, cache_only=True)
                    service_id = service.get_id()
                    ObjectRelations.servicegroup_services[servicegroup].add(service_id)
                    ObjectRelations.service_servicegroups[service_id].add(servicegroup)
                except Exception:
                    # If there is an error looking up any service, we ignore it and
                    # don't display it in a list of related services
                    pass


class ObjectFetcher(object):
    """
    This class is a wrapper around pynag.Parsers.config. Is responsible for fetching dict objects
    from config.data and turning into high ObjectDefinition objects

    Internal variables:
     _cached_objects = List of every ObjectDefinition
     _cached_id[o.get_id()] = o
     _cached_shortnames[o.object_type][o.get_shortname()] = o
     _cached_names[o.object_type][o.name] = o
     _cached_object_type[o.object_type].append( o )
    """
    _cached_objects = []
    _cached_ids = {}
    _cached_shortnames = defaultdict(dict)
    _cached_names = defaultdict(dict)
    _cached_object_type = defaultdict(list)

    def __init__(self, object_type):
        self.object_type = object_type

    def get_all(self):
        """ Return all object definitions of specified type"""
        if self.needs_reload():
            self.reload_cache()
        if self.object_type is not None:
            return ObjectFetcher._cached_object_type[self.object_type]
        else:
            return ObjectFetcher._cached_objects

    all = property(get_all)

    def reload_cache(self):
        """Reload configuration cache"""
        # clear object list
        ObjectFetcher._cached_objects = []
        ObjectFetcher._cached_ids = {}
        ObjectFetcher._cached_shortnames = defaultdict(dict)
        ObjectFetcher._cached_names = defaultdict(dict)
        ObjectFetcher._cached_object_type = defaultdict(list)
        global config
        if not config:
            config = Parsers.config(cfg_file)
        if config.needs_reparse():
            debug('Debug: Doing a reparse of configuration')
            config.parse()
            # Reset our list of how objects are related to each other
        ObjectRelations.reset()

        # Fetch all objects from Parsers.config
        for object_type, objects in config.data.items():
            # change "all_host" to just "host"
            object_type = object_type[len("all_"):]
            Class = string_to_class.get(object_type, ObjectDefinition)
            for i in objects:
                i = Class(item=i)
                ObjectFetcher._cached_objects.append(i)
                ObjectFetcher._cached_object_type[object_type].append(i)
                ObjectFetcher._cached_ids[i.get_id()] = i
                ObjectFetcher._cached_shortnames[i.object_type][i.get_shortname()] = i
                if i.name is not None:
                    ObjectFetcher._cached_names[i.object_type][i.name] = i
                i._do_relations()
        ObjectRelations.resolve_contactgroups()
        ObjectRelations.resolve_hostgroups()
        ObjectRelations.resolve_servicegroups()
        ObjectRelations.resolve_regex()
        return True

    def needs_reload(self):
        """ Returns true if configuration files need to be reloaded/reparsed """
        if ObjectFetcher._cached_objects == []:
            # we get here on first run
            return True
        elif config is None or config.needs_reparse():
            # We get here if any configuration file has changed
            return True
        return False

    def get_by_id(self, id):
        """ Get one specific object

        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        """
        if self.needs_reload():
            self.reload_cache()
        id = str(id).strip()
        return ObjectFetcher._cached_ids[id]

    def get_by_shortname(self, shortname, cache_only=False):
        """ Get one specific object by its shortname (i.e. host_name for host, etc)

        Arguments:
          shortname - shortname of the object. i.e. host_name, command_name, etc.
          cache_only -- If True, dont check if configuration files have changed since last parse

        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        """
        if not cache_only and self.needs_reload():
            self.reload_cache()
        shortname = str(shortname).strip()
        return ObjectFetcher._cached_shortnames[self.object_type][shortname]

    def get_by_name(self, object_name):
        """ Get one specific object by its object_name (i.e. name attribute)

        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        """
        if self.needs_reload():
            self.reload_cache()
        object_name = str(object_name).strip()
        return ObjectFetcher._cached_names[self.object_type][object_name]

    def get_object_types(self):
        """ Returns a list of all discovered object types """
        if config is None:
            self.reload_cache()
        return config.get_object_types()

    def filter(self, **kwargs):
        """
        Returns all objects that match the selected filter

        Examples:
        # Get all services where host_name is examplehost.example.com
        Service.objects.filter(host_name='examplehost.example.com')

        # Get service with host_name=examplehost.example.com and service_description='Ping'
        Service.objects.filter(host_name='examplehost.example.com',service_description='Ping')

        # Get all services that are registered but without a host_name
        Service.objects.filter(host_name=None,register='1')

        # Get all hosts that start with 'exampleh'
        Host.objects.filter(host_name__startswith='exampleh')

        # Get all hosts that end with 'example.com'
        Service.objects.filter(host_name__endswith='example.com')

        # Get all contactgroups that contain 'dba'
        Contactgroup.objects.filter(host_name__contains='dba')

        # Get all hosts that are not in the 'testservers' hostgroup
        Host.objects.filter(hostgroup_name__notcontains='testservers')

        # Get all services with non-empty name
        Service.objects.filter(name__isnot=None)

        # Get all hosts that have an address:
        Host.objects.filter(address_exists=True)

        """
        result = []
        # Lets convert all values to str()
        tmp = {}
        for k, v in kwargs.items():
            k = str(k)
            if v is not None:
                v = str(v)
            tmp[k] = v
        kwargs = tmp
        for i in self.all:
            object_matches = True
            negative_filter = False
            for k, v in kwargs.items():
                if k.endswith('__exists'):
                    k = k[:-len('__exists')]
                    object_matches = str(k in i) == str(v)
                    continue
                elif k.endswith('__startswith'):
                    k = k[:-12]
                    match_function = str.startswith
                elif k.endswith('__endswith'):
                    k = k[:-10]
                    match_function = str.endswith
                elif k.endswith('__isnot'):
                    k = k[:-7]
                    object_matches = str(i[k]) != str(v)
                    continue
                elif k.endswith('__contains'):
                    k = k[:-10]
                    match_function = contains
                elif k.endswith('__has_field'):
                    k = k[:-11]
                    match_function = has_field
                elif k.endswith('__notcontains'):
                    k = k[:-13]
                    match_function = not_contains
                    negative_filter = True
                else:
                    match_function = str.__eq__
                if not object_matches:
                    break
                if k == 'id' and str(v) != str(i.get_id()):
                    object_matches = False
                    break
                if k == 'register' and v == '1' and not k in i:
                    # not defined means item is registered
                    continue
                if v is None and k in i:
                    object_matches = False
                    break
                if not k in i:
                    if v is None:
                        continue  # if None was the search attribute
                    # Handle negated filter
                    if not negative_filter:
                        object_matches = False
                        break
                # Special case, if asking for a shortname and  there is an object with no shortname
                # we work around it so filter does not crash. However be aware that the config is invalid
                # if you have this
                if k == 'shortname' and not i[k]:
                    object_matches = False
                    break
                if not match_function(i[k], v):
                    object_matches = False
                    break
            if object_matches:
                result.append(i)
        return result


class ObjectDefinition(object):
    """
    Holds one instance of one particular Object definition
    Example usage:
        objects = ObjectDefinition.objects.all
        my_object ObjectDefinition( dict ) # dict = hash map of configuration attributes
    """
    object_type = None
    objects = ObjectFetcher(None)

    def __init__(self, item=None, filename=None, **kwargs):
        # Check if we have parsed the configuration yet
        if config is None:
            self.objects.reload_cache()
            # if Item is empty, we are creating a new object
        if item is None:
            item = config.get_new_item(object_type=self.object_type, filename=filename)
            self.is_new = True
        else:
            self.is_new = False

        # store the object_type (i.e. host,service,command, etc)
        self.object_type = item['meta']['object_type']

        # self.objects is a convenient way to access more objects of the same type
        self.objects = ObjectFetcher(self.object_type)

        # self.data -- This dict stores all effective attributes of this objects
        self._original_attributes = item

        #: _changes - This dict contains any changed (but yet unsaved) attributes of this object
        self._changes = {}

        #: _defined_attributes - All attributes that this item has defined
        self._defined_attributes = item['meta']['defined_attributes']

        #: _inherited_attributes - All attributes that this object has inherited via 'use'
        self._inherited_attributes = item['meta']['inherited_attributes']

        #: _meta - Various metadata about the object
        self._meta = item['meta']

        #: _macros - A dict object that resolves any particular Nagios Macro (i.e. $HOSTADDR$)
        self._macros = {}

        #: __argument_macros - A dict object that resolves $ARG* macros
        self.__argument_macros = {}

        # Any kwargs provided will be added to changes:
        for k, v in kwargs.items():
            self[k] = v

    def get_attribute(self, attribute_name):
        """Get one attribute from our object definition"""
        return self[attribute_name]

    def set_attribute(self, attribute_name, attribute_value):
        """Set (but does not save) one attribute in our object"""
        self[attribute_name] = attribute_value

    def is_dirty(self):
        """Returns true if any attributes has been changed on this object, and therefore it needs saving"""
        return len(self._changes.keys()) == 0

    def is_registered(self):
        """ Returns true if object is enabled (registered)
        """
        if not self.has_key('register'):
            return True
        if self['register'] is "1":
            return True
        return False

    def __cmp__(self, a, b):
        return cmp(a.get_description(), b.get_description())

    def __lt__(self, a, b):
        return a.get_description() < b.get_description()

    def __gt__(self, a, b):
        return a.get_description() > b.get_description()

    def __setitem__(self, key, item):
        # Special handle for macros
        if key.startswith('$') and key.endswith('$'):
            self.set_macro(key, item)
        elif self[key] != item:
            self._changes[key] = item
            self._event(level="debug", message="attribute changed: %s = %s" % (key, item))

    def __getitem__(self, key):
        if key == 'id':
            return self.get_id()
        elif key == 'description':
            return self.get_description()
        elif key == 'shortname':
            return self.get_shortname()
        elif key == 'effective_command_line':
            return self.get_effective_command_line()
        elif key == 'register' and not 'register' in self._defined_attributes:
            return "1"
        elif key == 'meta':
            return self._meta
        elif key in self._changes:
            return self._changes[key]
        elif key in self._defined_attributes:
            return self._defined_attributes[key]
        elif key in self._inherited_attributes:
            return self._inherited_attributes[key]
        elif key in self._meta:
            return self._meta[key]
        else:
            return None

    def __contains__(self, item):
        """ Returns true if item is in ObjectDefinition """
        if item in self.keys():
            return True
        if item in self._meta.keys():
            return True
        return False

    def has_key(self, key):
        """ Same as key in self
        """
        return key in self

    def keys(self):
        all_keys = ['meta', 'id', 'shortname', 'effective_command_line']
        for k in self._changes.keys():
            if k not in all_keys:
                all_keys.append(k)
        for k in self._defined_attributes.keys():
            if k not in all_keys:
                all_keys.append(k)
        for k in self._inherited_attributes.keys():
            if k not in all_keys:
                all_keys.append(k)
            #for k in self._meta.keys():
        #    if k not in all_keys: all_keys.append(k)
        return all_keys

    def items(self):
        return map(lambda x: (x, self[x]), self.keys())

    def get_id(self):
        """ Return a unique ID for this object"""
        #object_type = self['object_type']
        #shortname = self.get_description()
        #object_name = self['name']
        filename = self._original_attributes['meta']['filename']
        object_id = (filename, frozenset(self._defined_attributes.items()))
        return str(hash(object_id))

    def get_suggested_filename(self):
        """Returns a suitable configuration filename to store this object in

        Typical result value: str('/etc/nagios/pynag/templates/hosts.cfg')
        """
        # Invalid characters that might potentially mess with our path
        # | / ' " are all invalid. So is any whitespace
        invalid_chars = '[/\s\'\"\|]'
        object_type = re.sub(invalid_chars, '', self.object_type)
        description = re.sub(invalid_chars, '', self.get_description())
        # if pynag_directory is undefined, use "/pynag" dir under nagios.cfg
        global pynag_directory
        if pynag_directory is None:
            from os.path import dirname

            pynag_directory = dirname(config.cfg_file) + "/pynag"
            # templates go to the template directory
        if self['register'] == "0":
            path = "%s/templates/%ss/%s.cfg" % (pynag_directory, object_type, description)
        else:
            path = "%s/%ss/%s.cfg" % (pynag_directory, object_type, description)

            # Services go to same file as their host
            if object_type == 'service' and self.host_name is not None:
                try:
                    host = self.get_effective_hosts()[0]
                    path = host.get_filename()
                except Exception:
                    pass
                if self.host_name is not None:
                    # If we get here, host_name was specified, but it is an invalid host
                    host = re.sub(invalid_chars, '', self.host_name)
                    path = "%s/hosts/%s.cfg" % (pynag_directory, host)
        return path

    def save(self):
        """Saves any changes to the current object to its configuration file

        Returns:
            Number of changes made to the object
        """
        if config is None:
            self.objects.reload_cache()
        # Let event-handlers know we are about to save an object
        self._event(level='pre_save', message="%s '%s'." % (self.object_type, self['shortname']))
        # If this is a new object, we save it with config.item_add()
        number_of_changes = len(self._changes.keys())
        if self.is_new == True or self.get_filename() is None:
            if not self.get_filename():
                # discover a new filename
                self.set_filename(self.get_suggested_filename())
            for k, v in self._changes.items():
                if v is not None:  # Dont save anything if attribute is None
                    self._defined_attributes[k] = v
                    self._original_attributes[k] = v
                del self._changes[k]
            config.item_add(self._original_attributes, self.get_filename())
        else:
            # If we get here, we are making modifications to an object
            number_of_changes = 0
            for field_name, new_value in self._changes.items():
                save_result = config.item_edit_field(item=self._original_attributes, field_name=field_name,
                                                     new_value=new_value)
                if save_result == True:
                    del self._changes[field_name]
                    self._event(level='write',
                                message="%s changed from '%s' to '%s'" % (field_name, self[field_name], new_value))
                    if not new_value:
                        if field_name in self._defined_attributes:
                            del self._defined_attributes[field_name]
                        if field_name in self._original_attributes:
                            del self._original_attributes[field_name]
                    else:
                        self._defined_attributes[field_name] = new_value
                        self._original_attributes[field_name] = new_value
                    number_of_changes += 1
                else:
                    raise Exception(
                        "Failure saving object. filename=%s, object=%s" % (self.get_filename(), self['shortname']))

        # this piece of code makes sure that when we current object contains all current info
        self.reload_object()
        self._event(level='save', message="%s '%s' saved." % (self.object_type, self['shortname']))
        return number_of_changes

    def reload_object(self):
        """ Re applies templates to this object (handy when you have changed the use attribute """
        old_me = config.get_new_item(self.object_type, self.get_filename())
        old_me['meta']['defined_attributes'] = self._defined_attributes
        for k, v in self._defined_attributes.items():
            old_me[k] = v
        for k, v in self._changes.items():
            old_me[k] = v
        i = config._apply_template(old_me)
        new_me = self.__class__(item=i)
        self._defined_attributes = new_me._defined_attributes
        self._original_attributes = new_me._original_attributes
        self._inherited_attributes = new_me._inherited_attributes
        self._meta = new_me._meta

    def rewrite(self, str_new_definition=None):
        """ Rewrites this Object Definition in its configuration files.

        Arguments:
            str_new_definition = the actual string that will be written in the configuration file
            if str_new_definition is None, then we will use self.__str__()
        Returns:
            True on success
        """
        self._event(level='pre_save', message="Object definition is being rewritten")
        if self.is_new == True:
            self.save()
        if str_new_definition is None:
            str_new_definition = self._meta.get('raw_definition')
        config.item_rewrite(self._original_attributes, str_new_definition)
        self['meta']['raw_definition'] = str_new_definition
        self._event(level='write', message="Object definition rewritten")

        # this piece of code makes sure that when we current object contains all current info
        self.reload_object()
        self._event(level='save', message="Object definition was rewritten")
        return True

    def delete(self, recursive=False, cleanup_related_items=True):
        """ Deletes this object definition from its configuration files.

        Arguments:
            recursive: If True, look for items that depend on this object and delete them as well
            (for example, if you delete a host, delete all its services as well)

            cleanup_related_items: If True, look for related items and remove references to this one.
            (for example, if you delete a host, remove its name from all hostgroup.members entries)
        """
        self._event(level="pre_save", message="%s '%s' will be deleted." % (self.object_type, self.get_shortname()))
        if recursive == True:
            # Recursive does not have any meaning for a generic object, this should subclassed.
            pass
        result = config.item_remove(self._original_attributes)
        self._event(level="write", message="%s '%s' was deleted." % (self.object_type, self.get_shortname()))
        self._event(level="save", message="%s '%s' was deleted." % (self.object_type, self.get_shortname()))
        return result

    def copy(self, recursive=False, filename=None, **args):
        """ Copies this object definition with any unsaved changes to a new configuration object

        Arguments:
          filename: If specified, new object will be saved in this file.
          recursive: If true, also find any related children objects and copy those
          **args: Any argument will be treated a modified attribute in the new definition.
        Examples:
          myhost = Host.objects.get_by_shortname('myhost.example.com')

          # Copy this host to a new one
          myhost.copy( host_name="newhost.example.com", address="127.0.0.1")

          # Copy this host and all its services:
                    myhost.copy(recursive=True, host_name="newhost.example.com", address="127.0.0.1")

        Returns:
          * A copy of the new ObjectDefinition
          * A list of all copies objects if recursive == True
        """
        if args == {} and filename is None:
            raise ValueError('To copy an object definition you need at least one new attribute')

        new_object = string_to_class[self.object_type](filename=filename)
        for k, v in self._defined_attributes.items():
            new_object[k] = v
        for k, v in self._changes.items():
            new_object[k] = v
        for k, v in args.items():
            new_object[k] = v
        new_object.save()
        return new_object

    def get_related_objects(self):
        """ Returns a list of ObjectDefinition that depend on this object

        Object can "depend" on another by a 'use' or 'host_name' or similar attribute

        Returns:
            List of ObjectDefinition objects
        """
        result = []
        if self['name'] is not None:
            tmp = ObjectDefinition.objects.filter(use__has_field=self['name'], object_type=self['object_type'])
            for i in tmp:
                result.append(i)
        return result

    def __str__(self):
        return_buffer = "define %s {\n" % self.object_type
        fields = self._defined_attributes.keys()
        for i in self._changes.keys():
            if i not in fields:
                fields.append(i)
        fields.sort()
        interesting_fields = ['service_description', 'use', 'name', 'host_name']
        for i in interesting_fields:
            if i in fields:
                fields.remove(i)
                fields.insert(0, i)
        for key in fields:
            if key == 'meta' or key in self['meta'].keys():
                continue
            value = self[key]
            return_buffer += "  %-30s %s\n" % (key, value)
        return_buffer += "}\n"
        return return_buffer

    def __repr__(self):
        return "%s: %s" % (self['object_type'], self.get_description())

    def get(self, value, default=None):
        """ self.get(x) == self[x] """
        result = self[value]
        if result is None:
            return default
        else:
            return result

    def get_description(self):
        """ Returns a human friendly string describing current object.

        It will try the following in order:
        * return self.name (get the generic name)
        * return self get_shortname()
        * return "Untitled $object_type"
        """
        if self.name:
            return self.name
        if self.get_shortname():
            return self.get_shortname()
        return "Untitled %s" % self.object_type

    def get_shortname(self):
        """ Returns shortname of an object in string format.

        For the confused, nagios documentation refers to shortnames
        usually as <object_type>_name.

        * In case of Host it returns host_name
        * In case of Command it returns command_name
        * etc
        * Special case for services it returns "host_name/service_description"

        Returns None if no attribute can be found to use as a shortname
        """
        return self.get("%s_name" % self.object_type, None)

    def get_filename(self):
        """ Get name of the config file which defines this object
        """
        if self._meta['filename'] is None:
            return None
        return os.path.normpath(self._meta['filename'])

    def set_filename(self, filename):
        """ set name of the config file which this object will be written to on next save. """
        if filename is None:
            self._meta['filename'] = filename
        else:
            self._meta['filename'] = os.path.normpath(filename)

    def get_macro(self, macroname, host_name=None, contact_name=None):
        """ Take macroname (e.g. $USER1$) and return its actual value

        Arguments:
          macroname -- Macro that is to be resolved. For example $HOSTADDRESS$
          host_name -- Optionally specify host (use this for services that
                    -- don't define host specifically for example ones that only
                    -- define hostgroups
        Returns:
          (str) Actual value of the macro. For example "$HOSTADDRESS$" becomes "127.0.0.1"
        """
        if macroname.startswith('$ARG'):
            # Command macros handled in a special function
            return self._get_command_macro(macroname)
        if macroname.startswith('$USER'):
            # $USERx$ macros are supposed to be private, but we will display them anyway
            return config.get_resource(macroname)
        if macroname.startswith('$HOST') or macroname.startswith('$_HOST'):
            return self._get_host_macro(macroname, host_name=host_name)
        if macroname.startswith('$SERVICE') or macroname.startswith('$_SERVICE'):
            return self._get_service_macro(macroname)
        if macroname.startswith('$CONTACT') or macroname.startswith('$_CONTACT'):
            return self._get_contact_macro(macroname, contact_name=contact_name)
        if macroname in _standard_macros:
            attr = _standard_macros[macroname]
            return self[attr]
        return ''

    def set_macro(self, macroname, new_value):
        """ Update a macro (custom variable) like $ARG1$ intelligently

         Returns: None

         Notes: You are responsible for calling .save() after modifying the object

         Examples:
            >>> s = Service()
            >>> s.check_command = 'okc-execute!arg1!arg2'
            >>> s.set_macro('$ARG1$', 'modified1')
            >>> s.check_command
            'okc-execute!modified1!arg2'
            >>> s.set_macro('$ARG5$', 'modified5')
            >>> s.check_command
            'okc-execute!modified1!arg2!!!modified5'
            >>> s.set_macro('$_SERVICE_TEST$', 'test')
            >>> s['__TEST']
            'test'
        """
        if not macroname.startswith('$') or not macroname.endswith('$'):
            raise ValueError("Macros must be of the format $<macroname>$")
        if macroname.startswith('$ARG'):
            if self.check_command is None:
                raise ValueError("cant save %s, when there is no check_command defined" % macroname)
                # split check command into an array
            # in general the following will apply:
            # $ARG0$ = c[0]
            # $ARG1$ = c[1]
            # etc...
            c = self._split_check_command_and_arguments(self.check_command)
            arg_number = int(macroname[4:-1])
            # Special hack, if c array is to short for our value, we will make the array longer
            while arg_number >= len(c):
                c.append('')

            # Lets save our attribute
            c[arg_number] = new_value
            self.check_command = '!'.join(c)

        elif macroname.startswith('$_SERVICE'):
            macroname = "_" + macroname[9:-1]
            self[macroname] = new_value
        else:
            raise ValueError("No support for macro %s" % macroname)

    def get_all_macros(self):
        """Returns {macroname:macrovalue} hash map of this object's macros"""
        if self['check_command'] is None:
            return {}
        c = self['check_command']
        c = self._split_check_command_and_arguments(c)
        command_name = c.pop(0)
        command = Command.objects.get_by_shortname(command_name)
        regex = re.compile("(\$\w+\$)")
        macronames = regex.findall(command['command_line'])

        # Add all custom macros to our list:
        for i in self.keys():
            if not i.startswith('_'):
                continue
            if self.object_type == 'service':
                i = '$_SERVICE%s$' % (i[1:])
            elif self.object_type == 'host':
                i = '$_HOST%s$' % (i[1:])
            macronames.append(i)
        result = {}
        for i in macronames:
            result[i] = self.get_macro(i)
        return result

    def get_effective_command_line(self, host_name=None):
        """Return a string of this objects check_command with all macros (i.e. $HOSTADDR$) resolved"""
        if self['check_command'] is None:
            return None
        c = self['check_command']
        c = self._split_check_command_and_arguments(c)
        command_name = c.pop(0)
        try:
            command = Command.objects.get_by_shortname(command_name)
        except ValueError:
            return None
        return self._resolve_macros(command.command_line, host_name=host_name)

    def get_effective_notification_command_line(self, host_name=None, contact_name=None):
        """Return a string of this objects notifications with all macros (i.e. $HOSTADDR$) resolved

        Arguments:
            host_name    -- Simulate notification using this host. If None: Use first valid host (used for services)
            contact_name -- Simulate notification for this contact. If None: use first valid contact for the service
        """
        if contact_name is None:
            contacts = self.get_effective_contacts()
            if len(contacts) == 0:
                raise pynag.Utils.PynagError('Cannot calculate notification command for object with no contacts')
            else:
                contact = contacts[0]
        else:
            contact = Contact.objects.get_by_shortname(contact_name)

        notification_command = contact.service_notification_commands
        if not notification_command:
            return None

        command_name = notification_command.split('!').pop(0)
        try:
            command = Command.objects.get_by_shortname(command_name)
        except ValueError:
            return None
        return self._resolve_macros(command.command_line, host_name=host_name)

    def _resolve_macros(self, string, host_name=None):
        """ Returns string with every $NAGIOSMACRO$ resolved to actual value.

        Arguments:
            string    -- Arbitary string that contains macros
            host_name -- Optionally supply host_name if this service does not define it
        Example:
        >>> host = Host()
        >>> host.address = "127.0.0.1"
        >>> host._resolve_macros('check_ping -H $HOSTADDRESS$')
        'check_ping -H 127.0.0.1'
        """
        if not string:
            return None
        regex = re.compile("(\$\w+\$)")
        get_macro = lambda x: self.get_macro(x.group(), host_name=host_name)
        result = regex.sub(get_macro, string)
        return result

    def run_check_command(self, host_name=None):
        """Run the check_command defined by this service. Returns return_code,stdout,stderr"""

        command = self.get_effective_command_line(host_name=host_name)
        if command is None:
            return None
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
        stdout, stderr = proc.communicate('through stdin to stdout')
        return proc.returncode, stdout, stderr

    def _split_check_command_and_arguments(self, check_command):
        """ Split a nagios "check_command" string into a tuple

         >>> check_command = "check_ping!warning!critical"
         >>> o = ObjectDefinition()
         >>> o._split_check_command_and_arguments(check_command)
         ['check_ping', 'warning', 'critical']
         >>> complex_check_command = "check_ping!warning with \! in it!critical"
         >>> o._split_check_command_and_arguments(complex_check_command)
         ['check_ping', 'warning with \\\\! in it', 'critical']
        """
        if check_command in (None, ''):
            return []
        if '\!' in check_command:
            check_command = check_command.replace('\!', 'ESCAPE_EXCL_MARK')
        tmp = check_command.split('!')
        result = map(lambda x: x.replace('ESCAPE_EXCL_MARK', '\!'), tmp)
        return result

    def _get_command_macro(self, macroname, check_command=None):
        """Resolve any command argument ($ARG1$) macros from check_command"""
        if check_command is None:
            check_command = self.check_command
        if check_command is None:
            return ''
        all_args = {}
        c = self._split_check_command_and_arguments(check_command)
        c.pop(0)  # First item is the command, we dont need it
        for i, v in enumerate(c):
            name = '$ARG%s$' % str(i + 1)
            all_args[name] = v
        result = all_args.get(macroname, '')
        # Our $ARGx$ might contain macros on its own, so lets resolve macros in it:
        result = self._resolve_macros(result)
        return result

    def _get_service_macro(self, macroname):
        if macroname.startswith('$_SERVICE'):
            # If this is a custom macro
            name = macroname[9:-1]
            return self["_%s" % name]
        elif macroname in _standard_macros:
            attr = _standard_macros[macroname]
            return self[attr]
        elif macroname.startswith('$SERVICE'):
            name = macroname[8:-1].lower()
            return self.get(name) or ''
        return ''

    def _get_host_macro(self, macroname, host_name=None):
        if macroname.startswith('$_HOST'):
            # if this is a custom macro
            name = macroname[6:-1]
            return self["_%s" % name]
        elif macroname in _standard_macros:
            attr = _standard_macros[macroname]
            return self[attr]
        elif macroname.startswith('$HOST'):
            name = macroname[5:-1].lower()
            return self.get(name)
        return ''

    def _get_contact_macro(self, macroname, contact_name=None):
        # If contact_name is not specified, get first effective contact and resolve macro for that contact
        if not contact_name:
            contacts = self.get_effective_contacts()
            if len(contacts) == 0:
                return None
            contact = contacts[0]
        else:
            contact = Contact.objects.get_by_shortname(contact_name)
        return contact._get_contact_macro(macroname)

    def get_effective_children(self, recursive=False):
        """ Get a list of all objects that inherit this object via "use" attribute

        Arguments:
            recursive - If true, include grandchildren as well
        Returns:
            A list of ObjectDefinition objects
        """
        if not self.name:
            return []
        name = self.name
        children = self.objects.filter(use__has_field=name)
        if recursive == True:
            for i in children:
                grandchildren = i.get_effective_children(recursive)
                for grandchild in grandchildren:
                    if grandchild not in children:
                        children.append(grandchild)
        return children

    def get_effective_parents(self, recursive=False):
        """ Get all objects that this one inherits via "use" attribute

        Arguments:
            recursive - If true include grandparents in list to be returned
        Returns:
            a list of ObjectDefinition objects
        """
        if not self.use:
            return []
        results = []
        use = pynag.Utils.AttributeList(self.use)
        for parent_name in use:
            parent = self.objects.get_by_name(parent_name)
            if parent not in results:
                results.append(parent)
        if recursive is True:
            for i in results:
                grandparents = i.get_effective_parents(recursive=True)
                for gp in grandparents:
                    if gp not in results:
                        results.append(gp)
        return results

    def get_attribute_tuple(self):
        """ Returns all relevant attributes in the form of:

        (attribute_name,defined_value,inherited_value)
        """
        result = []
        for k in self.keys():
            inher = defin = None
            if k in self._inherited_attributes:
                inher = self._inherited_attributes[k]
            if k in self._defined_attributes:
                defin = self._defined_attributes[k]
            result.append((k, defin, inher))
        return result

    def get_parents(self):
        """ Out-dated, use get_effective_parents instead. Kept here for backwards compatibility """
        return self.get_effective_parents()

    def unregister(self, recursive=True):
        """ Short for self['register'] = 0 ; self.save() """
        self['register'] = 0
        self.save()
        if recursive is True:
            for i in self.get_related_objects():
                i.unregister()

    def attribute_appendfield(self, attribute_name, value):
        """Convenient way to append value to an attribute with a comma seperated value

        Example:
           >>> myservice = Service()
           >>> myservice.contact_groups = "+alladmins,localadmins"
           >>> myservice.attribute_appendfield(attribute_name="contact_groups", value='webmasters')
           >>> print myservice.contact_groups
           +alladmins,localadmins,webmasters
           """
        aList = AttributeList(self[attribute_name])

        # If list was empty before, add a + to it so we are appending to parent
        if len(aList.fields) == 0:
            aList.operator = '+'
        if value not in aList.fields:
            aList.fields.append(value)
            self[attribute_name] = str(aList)
        return

    def attribute_removefield(self, attribute_name, value):
        """Convenient way to remove value to an attribute with a comma seperated value

        Example:
           >>> myservice = Service()
           >>> myservice.contact_groups = "+alladmins,localadmins"
           >>> myservice.attribute_removefield(attribute_name="contact_groups", value='localadmins')
           >>> print myservice.contact_groups
           +alladmins
           """
        aList = AttributeList(self[attribute_name])

        if value in aList.fields:
            aList.fields.remove(value)
            self[attribute_name] = str(aList)
        return

    def attribute_replacefield(self, attribute_name, old_value, new_value):
        """Convenient way to replace field within an attribute with a comma seperated value

        Example:
           >>> myservice = Service()
           >>> myservice.contact_groups = "+alladmins,localadmins"
           >>> myservice.attribute_replacefield(attribute_name="contact_groups", old_value='localadmins', new_value="webmasters")
           >>> print myservice.contact_groups
           +alladmins,webmasters
           """
        aList = AttributeList(self[attribute_name])

        if old_value in aList.fields:
            i = aList.fields.index(old_value)
            aList.fields[i] = new_value
            self[attribute_name] = str(aList)
        return

    def _get_effective_attribute(self, attribute_name):
        """This helper function returns specific attribute, from this object or its templates

        This is handy for fields that effectively are many_to_many values.
        for example, "contactroups +group1,group2,group3"

        Fields that are known to use this format are:
            contacts, contactgroups, hostgroups, servicegroups, members,contactgroup_members
        """
        result = []
        tmp = self[attribute_name]
        if tmp is not None:
            result.append(tmp)
        if tmp is None or tmp.startswith('+'):
            for parent in self.get_parents():
                result.append(parent._get_effective_attribute(attribute_name))
                if parent[attribute_name] is not None and not parent[attribute_name].startswith('+'):
                    break
        return_value = []
        for value in result:
            value = value.strip('+')
            if value == '':
                continue
            if value not in return_value:
                return_value.append(value)
        tmp = ','.join(return_value)
        tmp = tmp.replace(',,', ',')
        return tmp

    def _event(self, level=None, message=None):
        """ Pass informational message about something that has happened within the Model """
        for i in eventhandlers:
            if level == 'write':
                i.write(object_definition=self, message=message)
            elif level == 'save':
                i.save(object_definition=self, message=message)
            elif level == 'pre_save':
                i.pre_save(object_definition=self, message=message)
            else:
                i.debug(object_definition=self, message=message)

    def _do_relations(self):
        """ Discover all related objects (f.e. services that belong to this host, etc

        ObjectDefinition only has relations via 'use' paramameter. Subclasses should extend this.
        """
        parents = AttributeList(self.use)
        for i in parents.fields:
            ObjectRelations.use[self.object_type][i].add(self.get_id())


class Host(ObjectDefinition):
    object_type = 'host'
    objects = ObjectFetcher('host')

    def acknowledge(self, sticky=1, notify=1, persistent=0, author='pynag', comment='acknowledged by pynag',
                    recursive=False):
        pynag.Control.Command.acknowledge_host_problem(host_name=self.host_name,
                                                       sticky=sticky,
                                                       notify=notify,
                                                       persistent=persistent,
                                                       author=author,
                                                       comment=comment,
                                                       timestamp=0,
                                                       command_file=config.get_cfg_value('command_file')
        )

    def downtime(self, start_time=None, end_time=None, trigger_id=0, duration=7200, author=None,
                 comment='Downtime scheduled by pynag', recursive=False):
        """ Put this object in a schedule downtime.

        Arguments:
          start_time -- When downtime should start. If None, use time.time() (now)
          end_time   -- When scheduled downtime should end. If None use start_time + duration
          duration   -- Alternative to end_time, downtime lasts for duration seconds. Default 7200 seconds.
          trigger_id -- trigger_id>0 means that this downtime should trigger another downtime with trigger_id.
          author     -- name of the contact scheduling downtime. If None, use current system user
          comment    -- Comment that will be put in with the downtime
          recursive -- Also schedule same downtime for all service of this host.

        Returns:
          None because commands sent to nagios have no return values

        Raises:
          PynagError if this does not look an active object.
        """
        if self.register == '0':
            raise pynag.Utils.PynagError('Cannot schedule a downtime for unregistered object')
        if not self.host_name:
            raise pynag.Utils.PynagError('Cannot schedule a downtime for host with no host_name')
        if start_time is None:
            start_time = time.time()
        if duration is None:
            duration = 7200
        duration = int(duration)
        if end_time is None:
            end_time = start_time + duration
        if author is None:
            author = getpass.getuser()
        arguments = {
            'host_name': self.host_name,
            'start_time': start_time,
            'end_time': end_time,
            'fixed': '1',
            'trigger_id': trigger_id,
            'duration': duration,
            'author': author,
            'comment': comment,
        }
        if recursive == True:
            pynag.Control.Command.schedule_host_svc_downtime(**arguments)
        else:
            pynag.Control.Command.schedule_host_downtime(**arguments)

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this Host """
        get_object = lambda x: Service.objects.get_by_id(x)
        list_of_shortnames = sorted(ObjectRelations.host_services[self.host_name])
        services = map(get_object, list_of_shortnames)
        # Look for services that define hostgroup_name that we belong to
        for hg in self.get_effective_hostgroups():
            services += hg.get_effective_services()
        return services

    def get_effective_contacts(self):
        """ Returns a list of all Contact that belong to this Host """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.host_contacts[self.host_name])
        return map(get_object, list_of_shortnames)

    def get_effective_contact_groups(self):
        """ Returns a list of all Contactgroup that belong to this Host """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.host_contact_groups[self.host_name])
        return map(get_object, list_of_shortnames)

    def get_effective_hostgroups(self):
        """ Returns a list of all Hostgroup that belong to this Host """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.host_hostgroups[self.host_name])
        return map(get_object, list_of_shortnames)

    def get_effective_network_parents(self, recursive=False):
        """ Get all objects this one depends on via "parents" attribute

        Arguments:
            recursive - If true include grandparents in list to be returned
        Returns:
            a list of ObjectDefinition objects
        """
        if self['parents'] is None:
            return []
        results = []
        parents = self['parents'].split(',')
        for parent_name in parents:
            results.append(self.objects.get_by_name(parent_name))
        if recursive is True:
            grandparents = []
            for i in results:
                grandparents.append(i.get_effective_network_parents(recursive=True))
            results += grandparents
        return results

    def get_effective_network_children(self, recursive=False):
        """ Get all objects that depend on this one via "parents" attribute

        Arguments:
            recursive - If true include grandchildren in list to be returned
        Returns:
            a list of ObjectDefinition objects
        """
        if self.host_name is None:
            return []
        children = self.objects.filter(parents__has_field=self.host_name)
        if recursive == True:
            for child in children:
                children += child.get_effective_network_children(recursive=True)
        return children

    def delete(self, recursive=False, cleanup_related_items=True):
        """ Overwrites ObjectDefinition.delete() so that recursive=True will delete all services as well """
        # Find all services and delete them as well
        if self.host_name is not None:
            if cleanup_related_items == True:
                for i in Hostgroup.objects.filter(members__has_field=self.host_name):
                    i.attribute_removefield('members', self.host_name)
                    i.save()
            if recursive == True:
                for i in Service.objects.filter(host_name__has_field=self.host_name, hostgroup_name__exists=False):
                # delete only services where only this host_name and no hostgroups are defined
                    i.delete(recursive=recursive)
            # Call parent to get delete myself
        super(self.__class__, self).delete(recursive=recursive)

    def get_related_objects(self):
        result = super(self.__class__, self).get_related_objects()
        if self['host_name'] is not None:
            tmp = Service.objects.filter(host_name=self['host_name'])
            for i in tmp:
                result.append(i)
        return result

    def get_effective_check_command(self):
        """ Returns a Command object as defined by check_command attribute

        Raises KeyError if check_command is not found or not defined.
        """
        c = self.check_command
        if not c or c == '':
            raise KeyError(None)
        check_command = c.split('!')[0]
        return Command.objects.get_by_shortname(check_command)

    def get_current_status(self):
        """ Same as Service.get_current_status() """
        return Status(self.host_name)

    def copy(self, recursive=False, filename=None, **args):
        """ Same as ObjectDefinition.copy() except can recursively copy services """
        copies = [ObjectDefinition.copy(self, recursive=recursive, filename=filename, **args)]
        if recursive is True and 'host_name' in args:
            for i in self.get_effective_services():
                copies.append(i.copy(filename=filename, host_name=args.get('host_name')))
        return copies

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        # Do hostgroups
        hg = AttributeList(self.hostgroups)
        for i in hg.fields:
            ObjectRelations.host_hostgroups[self.host_name].add(i)
            ObjectRelations.hostgroup_hosts[i].add(self.host_name)
            # Contactgroups
        cg = AttributeList(self.contact_groups)
        for i in cg.fields:
            ObjectRelations.host_contact_groups[self.host_name].add(i)
            ObjectRelations.contactgroup_hosts[i].add(self.get_id())
        contacts = AttributeList(self.contacts)
        for i in contacts.fields:
            ObjectRelations.host_contacts[self.host_name].add(i)
            ObjectRelations.contact_hosts[i].add(self.get_id())
        if self.check_command:
            command_name = self.check_command.split('!')[0]
            ObjectRelations.command_service[self.host_name].add(command_name)

    def add_to_hostgroup(self, hostgroup_name):
        """ Add host to a hostgroup """
        hostgroup = Hostgroup.objects.get_by_shortname(hostgroup_name)
        return _add_object_to_group(self, hostgroup)

    def remove_from_hostgroup(self, hostgroup_name):
        """ Removes host from specified hostgroup """
        hostgroup = Hostgroup.objects.get_by_shortname(hostgroup_name)
        return _remove_object_from_group(self, hostgroup)

    def add_to_contactgroup(self, contactgroup):
        return _add_to_contactgroup(self, contactgroup)

    def remove_from_contactgroup(self, contactgroup):
        return _remove_from_contactgroup(self, contactgroup)


class Service(ObjectDefinition):
    object_type = 'service'
    objects = ObjectFetcher('service')

    def get_shortname(self):
        if self.host_name and self.service_description:
            return "%s/%s" % (self['host_name'], self['service_description'])
        if self.service_description:
            return "%s" % (self['service_description'], )

        return None

    def _get_host_macro(self, macroname, host_name=None):
        if not host_name:
            host_name = self['host_name']
        if not host_name:
            return None
        try:
            myhost = Host.objects.get_by_shortname(host_name)
            return myhost._get_host_macro(macroname)
        except Exception:
            return None

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        # Do hostgroups
        hg = AttributeList(self.hostgroup_name)
        for i in hg.fields:
            ObjectRelations.service_hostgroups[self.get_id()].add(i)
            ObjectRelations.hostgroup_services[i].add(self.get_id())
            # Contactgroups
        cg = AttributeList(self.contact_groups)
        for i in cg.fields:
            ObjectRelations.service_contact_groups[self.get_id()].add(i)
            ObjectRelations.contactgroup_services[i].add(self.get_id())
        contacts = AttributeList(self.contacts)
        for i in contacts.fields:
            ObjectRelations.service_contacts[self.get_id()].add(i)
            ObjectRelations.contact_services[i].add(self.get_id())
        sg = AttributeList(self.servicegroups)
        for i in sg.fields:
            ObjectRelations.service_servicegroups[self.get_id()].add(i)
            ObjectRelations.servicegroup_services[i].add(self.get_id())
        if self.check_command:
            command_name = self.check_command.split('!')[0]
            ObjectRelations.command_service[self.get_id()].add(command_name)
        hosts = AttributeList(self.host_name)
        for i in hosts.fields:
            ObjectRelations.service_hosts[self.get_id()].add(i)
            ObjectRelations.host_services[i].add(self.get_id())

    def acknowledge(self, sticky=1, notify=1, persistent=0, author='pynag', comment='acknowledged by pynag',
                    timestamp=0):
        pynag.Control.Command.acknowledge_svc_problem(host_name=self.host_name,
                                                      service_description=self.service_description,
                                                      sticky=sticky,
                                                      notify=notify,
                                                      persistent=persistent,
                                                      author=author,
                                                      comment=comment,
                                                      timestamp=0,
                                                      command_file=config.get_cfg_value('command_file')
        )

    def downtime(self, start_time=None, end_time=None, trigger_id=0, duration=7200, author=None,
                 comment='Downtime scheduled by pynag', recursive=False):
        """ Put this object in a schedule downtime.

        Arguments:
          start_time -- When downtime should start. If None, use time.time() (now)
          end_time   -- When scheduled downtime should end. If None use start_time + duration
          duration   -- Alternative to end_time, downtime lasts for duration seconds. Default 7200 seconds.
          trigger_id -- trigger_id>0 means that this downtime should trigger another downtime with trigger_id.
          author     -- name of the contact scheduling downtime. If None, use current system user
          comment    -- Comment that will be put in with the downtime
          recursive  --  Here for compatibility. Has no effect on a service.

        Returns:
          None because commands sent to nagios have no return values

        Raises:
          PynagError if this does not look an active object.
        """
        if self.register == '0':
            raise pynag.Utils.PynagError('Cannot schedule a downtime for unregistered object')
        if not self.host_name:
            raise pynag.Utils.PynagError('Cannot schedule a downtime for service with no host_name')
        if not self.service_description:
            raise pynag.Utils.PynagError('Cannot schedule a downtime for service with service_description')
        if start_time is None:
            start_time = time.time()
        if duration is None:
            duration = 7200
        duration = int(duration)
        if end_time is None:
            end_time = start_time + duration
        if author is None:
            author = getpass.getuser()
        pynag.Control.Command.schedule_svc_downtime(
            host_name=self.host_name,
            service_description=self.service_description,
            start_time=start_time,
            end_time=end_time,
            fixed='1',
            trigger_id=trigger_id,
            duration=duration,
            author=author,
            comment=comment,
        )

    def get_effective_hosts(self):
        """ Returns a list of all Host that belong to this Service """
        get_object = lambda x: Host.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.service_hosts[self.get_id()])
        hosts = map(get_object, list_of_shortnames)
        for hg in self.get_effective_hostgroups():
            hosts += hg.get_effective_hosts()
        return hosts

    def get_effective_contacts(self):
        """ Returns a list of all Contact that belong to this Service """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.service_contacts[self.get_id()])
        return map(get_object, list_of_shortnames)

    def get_effective_contact_groups(self):
        """ Returns a list of all Contactgroup that belong to this Service """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.service_contact_groups[self.get_id()])
        return map(get_object, list_of_shortnames)

    def get_effective_hostgroups(self):
        """ Returns a list of all Hostgroup that belong to this Service """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.service_hostgroups[self.get_id()])
        return map(get_object, list_of_shortnames)

    def get_effective_servicegroups(self):
        """ Returns a list of all Servicegroup that belong to this Service """
        get_object = lambda x: Servicegroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.service_servicegroups[self.get_id()])
        return map(get_object, list_of_shortnames)

    def get_effective_check_command(self):
        """ Returns a Command object as defined by check_command attribute

        Raises KeyError if check_command is not found or not defined.
        """
        c = self.check_command
        if not c or c == '':
            raise KeyError(None)
        check_command = c.split('!')[0]
        return Command.objects.get_by_shortname(check_command)

    def get_current_status(self):
        """ Returns a Status object, reflecting this object status (i.e. status.dat)
        """
        return Status(self.host_name, self.service_description)

    def add_to_servicegroup(self, servicegroup_name):
        """ Add this service to a specific servicegroup
        """
        sg = Servicegroup.objects.get_by_shortname(servicegroup_name)
        return _add_object_to_group(self, sg)

    def remove_from_servicegroup(self, servicegroup_name):
        """ remove this service from a specific servicegroup
        """
        sg = Servicegroup.objects.get_by_shortname(servicegroup_name)
        return _remove_object_from_group(self, sg)

    def add_to_contactgroup(self, contactgroup):
        return _add_to_contactgroup(self, contactgroup)

    def remove_from_contactgroup(self, contactgroup):
        return _remove_from_contactgroup(self, contactgroup)


class Command(ObjectDefinition):
    object_type = 'command'
    objects = ObjectFetcher('command')


class Contact(ObjectDefinition):
    object_type = 'contact'
    objects = ObjectFetcher('contact')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['contact_name']

    def get_effective_contactgroups(self):
        """ Get a list of all Contactgroup that are hooked to this contact """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.contact_contactgroups[self.contact_name])
        return map(get_object, list_of_shortnames)

    def get_effective_hosts(self):
        """ Get a list of all Host that are hooked to this Contact """
        result = set()
        # First add all hosts that name this contact specifically
        get_object = lambda x: Host.objects.get_by_id(x)
        list_of_shortnames = sorted(ObjectRelations.contact_hosts[self.contact_name])
        result.update(map(get_object, list_of_shortnames))

        # Next do the same for all contactgroups this contact belongs in
        for i in self.get_effective_contactgroups():
            result.update(i.get_effective_hosts())
        return result

    def get_effective_services(self):
        """ Get a list of all Service that are hooked to this Contact """
        result = set()
        # First add all services that name this contact specifically
        get_object = lambda x: Service.objects.get_by_id(x)
        list_of_shortnames = sorted(ObjectRelations.contact_services[self.contact_name])
        result.update(map(get_object, list_of_shortnames))
        return result

    def _get_contact_macro(self, macroname):
        attribute_name = None
        if macroname in _standard_macros:
            attribute_name = _standard_macros.get(macroname)
        elif macroname.startswith('$_CONTACT'):
            # if this is a custom macro
            name = macroname[len('$_CONTACT'):-1]
            attribute_name = "_%s" % name
        elif macroname.startswith('$CONTACT'):
            # Lets guess an attribute for this macro
            # So convert $CONTACTEMAIL$ to email
            name = macroname[len('$CONTACT'):-1]
            attribute_name = name.lower()
        else:
            return ''
        return self.get(attribute_name) or ''

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        groups = AttributeList(self.contactgroups)
        for i in groups.fields:
            ObjectRelations.contact_contactgroups[self.contact_name].add(i)
            ObjectRelations.contactgroup_contacts[i].add(self.contact_name)

    def add_to_contactgroup(self, contactgroup):
        return _add_to_contactgroup(self, contactgroup)

    def remove_from_contactgroup(self, contactgroup):
        return _remove_from_contactgroup(self, contactgroup)


class ServiceDependency(ObjectDefinition):
    object_type = 'servicedependency'
    objects = ObjectFetcher('servicedependency')


class HostDependency(ObjectDefinition):
    object_type = 'hostdependency'
    objects = ObjectFetcher('hostdependency')


class Contactgroup(ObjectDefinition):
    object_type = 'contactgroup'
    objects = ObjectFetcher('contactgroup')

    def get_effective_contactgroups(self):
        """ Returns a list of every Contactgroup that is a member of this Contactgroup """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.contactgroup_subgroups[self.contactgroup_name])
        return map(get_object, list_of_shortnames)

    def get_effective_contacts(self):
        """ Returns a list of every Contact that is a member of this Contactgroup """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.contactgroup_contacts[self.contactgroup_name])
        return map(get_object, list_of_shortnames)

    def get_effective_hosts(self):
        """ Return every Host that belongs to this contactgroup """
        list_of_shortnames = sorted(ObjectRelations.contactgroup_hosts[self.contactgroup_name])
        get_object = lambda x: Host.objects.get_by_id(x)
        return map(get_object, list_of_shortnames)

    def get_effective_services(self):
        """ Return every Host that belongs to this contactgroup """
        services = {}
        for i in Service.objects.all:
            services[i.get_id()] = i
        list_of_shortnames = sorted(ObjectRelations.contactgroup_services[self.contactgroup_name])
        get_object = lambda x: services[x]
        return map(get_object, list_of_shortnames)

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        members = AttributeList(self.members)
        for i in members.fields:
            ObjectRelations.contactgroup_contacts[self.contactgroup_name].add(i)
            ObjectRelations.contact_contactgroups[i].add(self.contactgroup_name)
        groups = AttributeList(self.contactgroup_members)
        for i in groups.fields:
            ObjectRelations.contactgroup_contactgroups[self.contactgroup_name].add(i)

    def add_contact(self, contact_name):
        """ Adds one specific contact to this contactgroup. """
        contact = Contact.objects.get_by_shortname(contact_name)
        return _add_to_contactgroup(contact, self)

    def remove_contact(self, contact_name):
        """ Remove one specific contact from this contactgroup """
        contact = Contact.objects.get_by_shortname(contact_name)
        return _remove_from_contactgroup(contact, self)


class Hostgroup(ObjectDefinition):
    object_type = 'hostgroup'
    objects = ObjectFetcher('hostgroup')

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this hostgroup """
        list_of_shortnames = sorted(ObjectRelations.hostgroup_services[self.hostgroup_name])
        get_object = lambda x: Service.objects.get_by_id(x)
        return map(get_object, list_of_shortnames)

    def get_effective_hosts(self):
        """ Returns a list of all Host that belong to this hostgroup """
        list_of_shortnames = sorted(ObjectRelations.hostgroup_hosts[self.hostgroup_name])
        get_object = lambda x: Host.objects.get_by_shortname(x)
        return map(get_object, list_of_shortnames)

    def get_effective_hostgroups(self):
        """ Returns a list of every Hostgroup that is a member of this Hostgroup """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.hostgroup_subgroups[self.hostgroup_name])
        return map(get_object, list_of_shortnames)

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        members = AttributeList(self.members)
        for i in members.fields:
            ObjectRelations.hostgroup_hosts[self.hostgroup_name].add(i)
            ObjectRelations.host_hostgroups[i].add(self.hostgroup_name)
        groups = AttributeList(self.hostgroup_members)
        for i in groups.fields:
            ObjectRelations.hostgroup_hostgroups[self.hostgroup_name].add(i)

    def add_host(self, host_name):
        """ Adds host to this group. Behaves like Hostgroup._add_member_to_group """
        host = Host.objects.get_by_shortname(host_name)
        return _add_object_to_group(host, self)

    def remove_host(self, host_name):
        """ Remove host from this group. Behaves like Hostgroup._remove_member_from_group """
        host = Host.objects.get_by_shortname(host_name)
        return _remove_object_from_group(host, self)

    def delete(self, recursive=False, cleanup_related_items=True):
        """ Overwrites ObjectDefinition.delete() so that recursive=True will delete all services as well
            cleanup_related_items=True will also remove references in hostgroups,hosts + dependencies and escalations"""
        if self.hostgroup_name is not None:
            if recursive == True:
                for i in Service.objects.filter(hostgroup_name=self.hostgroup_name, host_name__exists=False):
                    #remove only if self.hostgroup_name is the only hostgroup and no host_name is specified
                    i.delete(recursive=recursive)
            if cleanup_related_items == True:
                hostgroups = Hostgroup.objects.filter(hostgroup_members__has_field=self.hostgroup_name)
                hosts = Host.objects.filter(hostgroups__has_field=self.hostgroup_name)
                dependenciesAndEscalations = ObjectDefinition.objects.filter(
                    hostgroup_name__has_field=self.hostgroup_name, object_type__isnot='hostgroup')
                dependencies = ObjectDefinition.objects.filter(dependent_hostgroup_name__has_field=self.hostgroup_name)
                for i in hostgroups:
                    # remove hostgroup from other hostgroups
                    i.attribute_removefield('hostgroup_members', self.hostgroup_name)
                    hgm = i.get_attribute('hostgroup_members')
                    # Remove the + character if it's the only thing remaining after removing a field from the hostgroup_members attribute
                    # Workaround for https://dev.icinga.org/issues/3900
                    if len(hgm) == 1 and hgm[0] == "+":
                        i.set_attribute('hostgroup_members', None)
                    i.save()
                for i in hosts:
                    # remove hostgroup from hosts
                    i.attribute_removefield('hostgroups', self.hostgroup_name)
                    i.save()
                for i in dependenciesAndEscalations:
                    # remove from host/service escalations/dependencies
                    i.attribute_removefield('hostgroup_name', self.hostgroup_name)
                    i.save()
                for i in dependencies:
                    # remove from host/service escalations/dependencies
                    i.attribute_removefield('dependent_hostgroup_name', self.hostgroup_name)
                    i.save()
            # Call parent to get delete myself
        super(self.__class__, self).delete(recursive=recursive)

    def downtime(self, start_time=None, end_time=None, trigger_id=0, duration=7200, author=None,
                 comment='Downtime scheduled by pynag', recursive=False):
        """ Put every host and service in this hostgroup in a schedule downtime.

        Arguments:
          start_time -- When downtime should start. If None, use time.time() (now)
          end_time   -- When scheduled downtime should end. If None use start_time + duration
          duration   -- Alternative to end_time, downtime lasts for duration seconds. Default 7200 seconds.
          trigger_id -- trigger_id>0 means that this downtime should trigger another downtime with trigger_id.
          author     -- name of the contact scheduling downtime. If None, use current system user
          comment    -- Comment that will be put in with the downtime
          recursive  -- For compatibility with other downtime commands, recursive is always assumed to be true

        Returns:
          None because commands sent to nagios have no return values

        Raises:
          PynagError if this does not look an active object.
        """
        if self.register == '0':
            raise pynag.Utils.PynagError('Cannot schedule a downtime for unregistered object')
        if not self.hostgroup_name:
            raise pynag.Utils.PynagError('Cannot schedule a downtime for hostgroup with no hostgroup_name')
        if start_time is None:
            start_time = time.time()
        if duration is None:
            duration = 7200
        duration = int(duration)
        if end_time is None:
            end_time = start_time + duration
        if author is None:
            author = getpass.getuser()
        arguments = {
            'hostgroup_name': self.hostgroup_name,
            'start_time': start_time,
            'end_time': end_time,
            'fixed': '1',
            'trigger_id': trigger_id,
            'duration': duration,
            'author': author,
            'comment': comment,
        }
        pynag.Control.Command.schedule_hostgroup_host_downtime(**arguments)
        pynag.Control.Command.schedule_hostgroup_svc_downtime(**arguments)


class Servicegroup(ObjectDefinition):
    object_type = 'servicegroup'
    objects = ObjectFetcher('servicegroup')

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this Servicegroup """
        list_of_shortnames = sorted(ObjectRelations.servicegroup_services[self.servicegroup_name])
        get_object = lambda x: Service.objects.get_by_id(x)
        return map(get_object, list_of_shortnames)

    def get_effective_servicegroups(self):
        """ Returns a list of every Servicegroup that is a member of this Servicegroup """
        get_object = lambda x: Servicegroup.objects.get_by_shortname(x)
        list_of_shortnames = sorted(ObjectRelations.servicegroup_subgroups[self.servicegroup_name])
        return map(get_object, list_of_shortnames)

    def add_service(self, shortname):
        """ Adds service to this group. Behaves like _add_object_to_group(object, group)"""
        service = Service.objects.get_by_shortname(shortname)
        return _add_object_to_group(service, self)

    def remove_service(self, shortname):
        """ remove service from this group. Behaves like _remove_object_from_group(object, group)"""
        service = Service.objects.get_by_shortname(shortname)
        return _remove_object_from_group(service, self)

    def _do_relations(self):
        super(self.__class__, self)._do_relations()

        # Members directive for the servicegroup is members = host1,service1,host2,service2,...,hostn,servicen
        members = AttributeList(self.members).fields
        while len(members) > 1:
            host_name = members.pop(0)
            service_description = members.pop(0)
            shortname = '%s/%s' % (host_name, service_description)
            ObjectRelations.servicegroup_members[self.servicegroup_name].add(shortname)
            # Handle servicegroup_members
        groups = AttributeList(self.servicegroup_members)
        for i in groups.fields:
            ObjectRelations.servicegroup_servicegroups[self.servicegroup_name].add(i)

    def downtime(self, start_time=None, end_time=None, trigger_id=0, duration=7200, author=None,
                 comment='Downtime scheduled by pynag', recursive=False):
        """ Put every host and service in this servicegroup in a schedule downtime.

        Arguments:
          start_time -- When downtime should start. If None, use time.time() (now)
          end_time   -- When scheduled downtime should end. If None use start_time + duration
          duration   -- Alternative to end_time, downtime lasts for duration seconds. Default 7200 seconds.
          trigger_id -- trigger_id>0 means that this downtime should trigger another downtime with trigger_id.
          author     -- name of the contact scheduling downtime. If None, use current system user
          comment    -- Comment that will be put in with the downtime
          recursive  -- For compatibility with other downtime commands, recursive is always assumed to be true

        Returns:
          None because commands sent to nagios have no return values

        Raises:
          PynagError if this does not look an active object.
        """
        if self.register == '0':
            raise pynag.Utils.PynagError('Cannot schedule a downtime for unregistered object')
        if not self.servicegroup_name:
            raise pynag.Utils.PynagError('Cannot schedule a downtime for servicegroup with no servicegroup_name')
        if start_time is None:
            start_time = time.time()
        if duration is None:
            duration = 7200
        duration = int(duration)
        if end_time is None:
            end_time = start_time + duration
        if author is None:
            author = getpass.getuser()
        arguments = {
            'servicegroup_name': self.servicegroup_name,
            'start_time': start_time,
            'end_time': end_time,
            'fixed': '1',
            'trigger_id': trigger_id,
            'duration': duration,
            'author': author,
            'comment': comment,
        }
        pynag.Control.Command.schedule_servicegroup_host_downtime(**arguments)
        pynag.Control.Command.schedule_servicegroup_svc_downtime(**arguments)


class Timeperiod(ObjectDefinition):
    object_type = 'timeperiod'
    objects = ObjectFetcher('timeperiod')


class Status(object):
    """ Contains current status info (i.e. status.dat) for one specific Host or Service """
    plugin_output = ''
    perfdata = ''
    long_plugin_output = ''
    current_state = ''
    perfdatalist = []

    def __init__(self, host_name, service_description=None):
        self.host_name = host_name
        s = Parsers.status()
        s.parse()
        try:
            if not service_description:
                # This is a host status
                self.status = s.get_hoststatus(host_name)
            else:
                # This is a service status
                self.status = s.get_servicestatus(host_name, service_description)
        except ValueError:
            self.status = None
        self.plugin_output = self.status['plugin_output']
        self.perfdata = self.status['performance_data']
        self.long_plugin_output = self.status['long_plugin_output']
        self.current_state = self.status['current_state']
        self.perfdatalist = pynag.Utils.PerfData(self.perfdata)


def _add_object_to_group(my_object, my_group):
    """ Add one specific object to a specified objectgroup

    Examples:
    c = Contact()
    g = Contactgroup()

    _add_to_group(c, g )
    """
    # First of all, we behave a little differently depending on what type of an object we lets define some variables:
    object_type = my_object.object_type     # contact,host,service, etc

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
        # Remove object from the group
        my_group.attribute_removefield(group_field, object_name)
        my_group.save()

    if object_name in list_of_members:
        # Remove group from the object
        my_object.attribute_removefield(object_field, group_name)
        my_object.save()


def _add_to_contactgroup(my_object, contactgroup):
    """ add Host or Service to a contactgroup
    """
    if type(contactgroup) == type(str):
        contactgroup = Contactgroup.get_by_shortname(contactgroup)

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
    if type(contactgroup) == type(str):
        contactgroup = Contactgroup.get_by_shortname(contactgroup)

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


class HostStatus(Status):
    """ Contains Status info (i.e. status.dat) for one specific Host """

    def __init__(self, data):
        self.data = data
        self.plugin_output = self.data['plugin_output']
        self.perfdata = self.data['performance_data']
        self.long_plugin_output = self.data['long_plugin_output']
        self.current_state = self.data['current_state']
        self.perfdatalist = pynag.Utils.PerfData(self.perfdata)

    def get_shortname(self):
        return self.data['host_name']

    def __str__(self):
        return "%s - %s" % (self.get_shortname(), self.get_state())

    def get_state(self):
        return self.data['current_state']

    def __repr__(self):
        return self.__str__()


class StatusFetcher(object):
    """ Responsible for fetching multiple Status objects (from status.dat, mk-livestatus, etc) """
    _cached_objects = []
    _cached_shortnames = defaultdict(dict)
    _cached_object_type = defaultdict(list)
    object_type = None

    def __init__(self, object_type):
        """
        """
        self.object_type = object_type

    def get_all(self):
        """ Return all object definitions of specified type"""
        if self.needs_reload():
            self.reload_cache()
        if self.object_type is not None:
            return StatusFetcher._cached_object_type[self.object_type]
        else:
            return StatusFetcher._cached_objects

    all = property(get_all)

    def needs_reload(self):
        """ Returns True if cached status data is out of date """
        return True

    def reload_cache(self):
        """Reload status cache"""
        status = Parsers.status()
        status.parse()

        # Fetch all objects from Parsers.config
        for object_type, objects in status.data.items():
            for i in objects:
                if object_type == 'hoststatus':
                    item = HostStatus(data=i)
                else:
                    continue
                    #item = Status(data=i)
                StatusFetcher._cached_objects.append(item)
                StatusFetcher._cached_object_type[object_type].append(item)
                StatusFetcher._cached_shortnames[object_type][item.get_shortname()] = item
        return True


string_to_class = {}
string_to_class['contact'] = Contact
string_to_class['service'] = Service
string_to_class['host'] = Host
string_to_class['hostgroup'] = Hostgroup
string_to_class['contactgroup'] = Contactgroup
string_to_class['servicegroup'] = Servicegroup
string_to_class['timeperiod'] = Timeperiod
string_to_class['hostdependency'] = HostDependency
string_to_class['servicedependency'] = ServiceDependency
string_to_class['command'] = Command
#string_to_class[None] = ObjectDefinition

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
    fget = lambda self: self.get_attribute(name)
    fset = lambda self, value: self.set_attribute(name, value)
    fdel = lambda self: self.set_attribute(name, None)
    fdoc = "This is the %s attribute for object definition"
    setattr(ClassType, name, property(fget, fset, fdel, fdoc))


# Add register, name and use to all objects
_add_property(ObjectDefinition, 'register')
_add_property(ObjectDefinition, 'name')
_add_property(ObjectDefinition, 'use')

# For others, create attributes dynamically based on all_attributes.keys()
for object_type, attributes in all_attributes.object_definitions.items():
    # Lets find common attributes that every object definition should have:
    if object_type == 'any':
        continue
    if object_type not in string_to_class:
        continue
    Object = string_to_class[object_type]

    for attribute in attributes:
        _add_property(Object, attribute)

if __name__ == '__main__':
    o = Hostgroup.objects.filter(shortname__contains='t')
