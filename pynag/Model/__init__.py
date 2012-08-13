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

from pynag import Parsers
from macros import _standard_macros
from collections import defaultdict
import all_attributes

# Path To Nagios configuration file
cfg_file = None  # '/etc/nagios/nagios.cfg'

# Were new objects are written by default
pynag_directory = '/etc/nagios/pynag'

# This will be a Parsers.config instance once we have parsed 
config = None 
#config.parse()


#: eventhandlers -- A list of Model.EventHandelers object.
# Event handler is responsible for passing notification whenever something
# important happens in the model.
#
# For example FileLogger class is an event handler responsible for logging to
# file whenever something has been written.
eventhandlers = []


def debug(text):
    if debug == True: print text


def contains(str1, str2):
    """Returns True if str1 contains str2"""
    if not str1:
        return False
    if str1.find(str2) > -1: return True


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
    if str2 in str1: return True
    return False


class ObjectRelations(object):
    """ Static container for objects and their respective neighbours """
    # c['contact_name'] = ['host_name1','host_name2']
    contact_hosts = defaultdict(set)

    # c['contact_name'] = ['contactgroup1','contactgroup2']
    contact_contactgroups = defaultdict(set)

    # c['contact_name'] = ['service1.get_id()','service2.get_id()']
    contact_services = defaultdict(set)

    # c['contactgroup_name'] = ['contact1.contact_name','contact2.contact_name','contact3.contact_name']
    contactgroup_contacts = defaultdict(set)

    # c['contactgroup_name'] = ['contactgroup1','contactgroup2','contactgroup3']
    contactgroup_contactgroups = defaultdict(set)

    # c['contactgroup_name'] = ['host_name1', 'host_name2']
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

    # c[command_name] = '['service.get_id()','service.get_id()']
    command_service = defaultdict(set)

    # c[command_name] = '['host_name1','host_name2']
    command_host = defaultdict(set)

    # use['host']['host_name1'] = ['host_name2','host_name3']
    # use['contact']['contact_name1'] = ['contact_name2','contact_name3']
    _defaultdict_set = lambda: defaultdict(set)

    #
    contactgroup_subgroups = defaultdict(set)
    use = defaultdict( _defaultdict_set )

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
                subgroups.update( dictname[i] )
        return checked_groups

    @staticmethod
    def resolve_contactgroups():
        """ Update all contactgroup relations to take into account contactgroup.contactgroup_members """
        groups = ObjectRelations.contactgroup_contactgroups.keys()
        for group in groups:
            subgroups = ObjectRelations._get_subgroups(group, ObjectRelations.contactgroup_contactgroups)
            ObjectRelations.contactgroup_subgroups[group] = subgroups

            # Loop through every subgroup and apply its attributes to ours
            for subgroup in subgroups:
                for i in ObjectRelations.contactgroup_contacts[group]:
                    ObjectRelations.contact_contactgroups[i].add( group )
                for i in ObjectRelations.contactgroup_hosts[group]:
                    ObjectRelations.host_contact_groups[i].add( group )
                for i in ObjectRelations.contactgroup_services[group]:
                    ObjectRelations.service_contact_groups[i].add( group )
                ObjectRelations.contactgroup_contacts[group].update( ObjectRelations.contactgroup_contacts[subgroup] )
                ObjectRelations.contactgroup_hosts[group].update( ObjectRelations.contactgroup_hosts[subgroup] )
                ObjectRelations.contactgroup_services[group].update( ObjectRelations.contactgroup_services[subgroup] )

    @staticmethod
    def resolve_hostgroups():
        """ Update all hostgroup relations to take into account hostgroup.hostgroup_members """
        groups = ObjectRelations.hostgroup_hostgroups.keys()
        for group in groups:
            subgroups = ObjectRelations._get_subgroups(group, ObjectRelations.hostgroup_hostgroups)
            ObjectRelations.hostgroup_subgroups[group] = subgroups

            # Loop through every subgroup and apply its attributes to ours
            for subgroup in subgroups:
                for i in ObjectRelations.hostgroup_hosts[group]:
                    ObjectRelations.host_hostgroups[i].add( group )
                for i in ObjectRelations.hostgroup_services[group]:
                    ObjectRelations.service_hostgroups[i].add( group )
                ObjectRelations.hostgroup_hosts[group].update( ObjectRelations.hostgroup_hosts[subgroup] )
                ObjectRelations.hostgroup_services[group].update( ObjectRelations.hostgroup_services[subgroup] )


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

        # Fetch all objects from Parsers.config
        for object_type, objects in config.data.items():
            # change "all_host" to just "host"
            object_type = object_type[ len("all_"): ]
            Class = string_to_class.get( object_type, ObjectDefinition )
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
        id = str(id)
        return ObjectFetcher._cached_ids[id]

    def get_by_shortname(self, shortname):
        """ Get one specific object by its shortname (i.e. host_name for host, etc)

        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        """
        if self.needs_reload():
            self.reload_cache()
        shortname = str(shortname)
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
        return ObjectFetcher._cached_names[self.object_type][object_name]

    def get_object_types(self):
        """ Returns a list of all discovered object types """
        if config is None: self.reload_cache()
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
        for k,v in kwargs.items():
            k = str(k)
            if v is not None: v = str(v)
            tmp[k] = v
        kwargs = tmp
        for i in self.all:
            object_matches = True
            for k, v in kwargs.items():
                if k.endswith('__exists'):
                    k = k[:-len('__exists')]
                    object_matches = str(i.has_key(k)) == str(v)
                    break
                elif k.endswith('__startswith'):
                    k = k[:-12]
                    match_function = str.startswith
                elif k.endswith('__endswith'):
                    k = k[:-10]
                    match_function = str.endswith
                elif k.endswith('__isnot'):
                    k = k[:-7]
                    match_function = str.__ne__
                elif k.endswith('__contains'):
                    k = k[:-10]
                    match_function = contains
                elif k.endswith('__has_field'):
                    k = k[:-11]
                    match_function = has_field
                elif k.endswith('__notcontains'):
                    k = k[:-13]
                    match_function = not_contains
                else:
                    match_function = str.__eq__
                if k == 'id' and str(v) == str(i.get_id()):
                    object_matches = True
                    break
                if k == 'register' and v == '1' and not i.has_key(k):
                    # not defined means item is registered
                    continue
                if v is None and i.has_key(k):
                    object_matches = False
                    break
                if not i.has_key(k):
                    if v is None: continue # if None was the search attribute
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

    def __init__(self, item=None, filename=None):
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

        # Lets find common attributes that every object definition should have:
        self._add_property('register')
        self._add_property('name')
        self._add_property('use')
        
        defs = all_attributes.object_definitions.get(self.object_type,{})
        for k in defs.keys():
            self._add_property(k)
    
    def _add_property(self, name):
        """ Creates dynamic properties for every attribute of out definition.

        i.e. this makes sure host_name attribute is accessable as self.host_name

        Returns: None
        """
        fget = lambda self: self.get_attribute(name)
        fset = lambda self, value: self.set_attribute(name, value)
        fdel = lambda self: self.set_attribute(name, None)
        fdoc = "This is the %s attribute for object definition"
        setattr( self.__class__, name, property(fget,fset,fdel,fdoc))

    def get_attribute(self, attribute_name):
        """Get one attribute from our object definition"""
        return self[attribute_name]

    def set_attribute(self, attribute_name, attribute_value):
        """Set (but does not save) one attribute in our object"""
        self[attribute_name] = attribute_value
        self._event(level="debug", message="attribute changed: %s = %s" % (attribute_name, attribute_value))

    def is_dirty(self):
        """Returns true if any attributes has been changed on this object, and therefore it needs saving"""
        return len(self._changes.keys()) == 0

    def is_registered(self):
        """ Returns true if object is enabled (registered)
        """
        if not self.has_key('register'): return True
        if self['register'] is "1": return True
        return False

    def __setitem__(self, key, item):
        self._changes[key] = item

    def __getitem__(self, key):
        if key == 'id':
            return self.get_id()
        if key == 'description' or key == 'shortname':
            return self.get_description()
        if key == 'register' and not self._defined_attributes.has_key('register'):
            return "1"
        if key == 'meta':
            return self._meta
        if self._changes.has_key(key):
            return self._changes[key]
        elif self._defined_attributes.has_key(key):
            return self._defined_attributes[key]
        elif self._inherited_attributes.has_key(key):
            return self._inherited_attributes[key]
        elif self._meta.has_key(key):
            return self._meta[key]
        else:
            return None

    def has_key(self, key):
        if key in self.keys():
            return True
        if key in self._meta.keys():
            return True
        return False

    def keys(self):
        all_keys = ['meta']
        for k in self._changes.keys():
            if k not in all_keys: all_keys.append(k)
        for k in self._defined_attributes.keys():
            if k not in all_keys: all_keys.append(k)
        for k in self._inherited_attributes.keys():
            if k not in all_keys: all_keys.append(k)
        #for k in self._meta.keys():
        #    if k not in all_keys: all_keys.append(k)
        return all_keys

    def get_id(self):
        """ Return a unique ID for this object"""
        object_type = self['object_type']
        shortname = self.get_description()
        object_name = self['name']
        filename = self['filename']
        object_id = "%s-%s-%s-%s" % ( object_type, shortname, object_name, filename)
        return str(object_id.__hash__())

    def get_suggested_filename(self):
        """Returns a suitable configuration filename to store this object in

        Typical result value: str('/etc/nagios/pynag/templates/hosts.cfg')
        """
        object_type = self.object_type
        shortname = self.get_shortname()
        if self['register'] == "0":
            # This is a template
            path = "%s/templates/%ss.cfg" % (pynag_directory, object_type)
        else:
            # Not a template
            if object_type == 'service':
                # Services written in same file as their host
                shortname = self['host_name']
            path = "%s/%ss/%s.cfg" % (pynag_directory, object_type, shortname)
        return path

    def save(self):
        """Saves any changes to the current object to its configuration file
        
        Returns:
            Number of changes made to the object
        """
        if config is None: self.objects.reload_cache()
        # If this is a new object, we save it with config.item_add()
        number_of_changes = len(self._changes.keys())
        if self.is_new is True or self.get_filename() is None:
            if not self.get_filename():
                # discover a new filename
                self.set_filename( self.get_suggested_filename() )
            for k,v in self._changes.items():
                self._defined_attributes[k] = v
                self._original_attributes[k] = v
                del self._changes[k]
            config.item_add(self._original_attributes, self.get_filename())
        else:
            # If we get here, we are making modifications to an object
            number_of_changes = 0
            for field_name, new_value in self._changes.items():
                save_result = config.item_edit_field(item=self._original_attributes, field_name=field_name, new_value=new_value)
                if save_result == True:
                    del self._changes[field_name]
                    self._event(level='save', message="%s changed from '%s' to '%s'" % (field_name, self[field_name], new_value))
                    if not new_value:
                        if self._defined_attributes.has_key(field_name):
                            del self._defined_attributes[field_name]
                        if self._original_attributes.has_key(field_name):
                            del self._original_attributes[field_name]
                    else:
                        self._defined_attributes[field_name] = new_value
                        self._original_attributes[field_name] = new_value
                    number_of_changes += 1
                else:
                    raise Exception("Failure saving object. filename=%s, object=%s" % (self.get_filename(), self['shortname']) )

        # this piece of code makes sure that when we current object contains all current info
        self.reload_object()
        self._event(level='write', message="%s '%s'." % (self.object_type, self['shortname'] ))
        return number_of_changes
    
    def reload_object(self):
        """ Re applies templates to this object (handy when you have changed the use attribute """
        old_me = config.get_new_item(self.object_type, self.get_filename())
        old_me['meta']['defined_attributes'] = self._defined_attributes
        for k,v in self._defined_attributes.items():
            old_me[k] = v
        for k,v in self._changes.items():
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
        if str_new_definition is None:
            str_new_definition = self._meta.get('raw_definition')
        config.item_rewrite(self._original_attributes, str_new_definition)
        self['meta']['raw_definition'] = str_new_definition
        self._event(level='write', message="Object definition rewritten")

        # this piece of code makes sure that when we current object contains all current info
        self.reload_object()
        return True

    def delete(self, recursive=False ):
        """ Deletes this object definition from its configuration files.
        
        Arguments:
            recursive: If True, look for items that depend on this object and delete them as well
            (for example, if you delete a host, delete all its services as well)
        """
        if recursive == True:
            # Recursive does not have any meaning for a generic object, this should subclassed.
            pass
        result = config.item_remove(self._original_attributes)
        self._event(level="write", message="Object was deleted")
        return result

    def copy(self, recursive=False,filename=None, **args):
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
          A copy of the new ObjectDefinition
        """
        if args == {}:
                raise ValueError('To copy an object definition you need at least one new attribute')
        
        new_object = string_to_class[self.object_type]( filename=filename )
        for k,v in self._defined_attributes.items():
            new_object[k] = v
        for k,v in self._changes.items():
            new_object[k] = v
        for k,v in args.items():
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
            for i in tmp: result.append(i)
        return result

    def __str__(self):
        return_buffer = "define %s {\n" % self.object_type
        fields = self._defined_attributes.keys()
        for i in self._changes.keys():
            if i not in fields: fields.append(i)
        fields.sort()
        interesting_fields = ['service_description', 'use', 'name', 'host_name']
        for i in interesting_fields:
            if i in fields:
                fields.remove(i)
                fields.insert(0, i)           
        for key in fields:
            if key == 'meta' or key in self['meta'].keys(): continue
            value = self[key]
            return_buffer += "  %-30s %s\n" % (key, value)
        return_buffer += "}\n"
        return return_buffer

    def __repr__(self):
        return "%s: %s" % (self['object_type'], self.get_shortname())

    def get(self, value, default=None):
        """ self.get(x) == self[x] """
        if self.has_key(value): return self[value]
        return default

    def get_description(self):
        return self.get("%s_name" % self.object_type, None)

    def get_shortname(self):
        return self.get_description()

    def get_filename(self):
        """ Get name of the config file which defines this object
        """
        if self._meta['filename'] is None: return None
        return os.path.normpath( self._meta['filename'] )

    def set_filename(self, filename):
        """ set name of the config file which defines this object"""
        if filename is None:
            self._meta['filename'] = filename
        else:
            self._meta['filename'] = os.path.normpath( filename )

    def get_macro(self, macroname, host_name=None ):
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
        if _standard_macros.has_key( macroname ):
            attr = _standard_macros[ macroname ]
            return self[ attr ]
        return ''

    def get_all_macros(self):
        """Returns {macroname:macrovalue} hash map of this object's macros"""
        # TODO: This function is incomplete and untested
        if self['check_command'] is None: return None
        c = self['check_command']
        c = c.split('!')
        command_name = c.pop(0)
        command = Command.objects.get_by_shortname(command_name)
        regex = re.compile("(\$\w+\$)")
        macronames = regex.findall( command['command_line'] )
        
        # Add all custom macros to our list:
        for i in self.keys():
            if not i.startswith('_'): continue
            if self.object_type == 'service':
                i = '$_SERVICE%s$' % (i[1:])
            elif self.object_type == 'host':
                i = '$_HOST%s$' % (i[1:])
            macronames.append( i )
        result = {}
        for i in macronames:
            result[i] = self.get_macro(i)
        return result

    def get_effective_command_line(self, host_name=None):
        """Return a string of this objects check_command with all macros (i.e. $HOSTADDR$) resolved"""
        # TODO: This function is incomplete and untested
        if self['check_command'] is None: return None
        c = self['check_command']
        c = c.split('!')
        command_name = c.pop(0)
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
        >>> i._resolve_macros('$USER1$/check_ping -H $HOSTADDRESS')
        '/usr/lib64/nagios/plugins/check_ping -H 127.0.0.1'
        """
        regex = re.compile("(\$\w+\$)")
        get_macro = lambda x: self.get_macro(x.group(), host_name=host_name)
        result = regex.sub(get_macro, string)
        return result

    def run_check_command(self, host_name=None):
        """Run the check_command defined by this service. Returns return_code,stdout,stderr"""
        
        command = self.get_effective_command_line(host_name=host_name)
        if command is None: return None
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate('through stdin to stdout')
        return proc.returncode,stdout,stderr

    def _get_command_macro(self, macroname):
        """Resolve any command argument ($ARG1$) macros from check_command"""
        # TODO: This function is incomplete and untested
        a = self.__argument_macros
        if a == {}:
            c = self['check_command'].split('!')
            c.pop(0) # First item is the command, we dont need it
            for i, v in enumerate( c ):
                tmp = i+1
                if v.startswith('$') and v.endswith('$') and not v.startswith('$ARG'):
                    v = self.get_macro(v)
                a['$ARG%s$' % tmp] = v
        result = a.get(macroname, '')
        # Our $ARGx$ might contain macros on its own, so lets resolve macros in it:
        result = self._resolve_macros(result)
        return result

    def _get_service_macro(self,macroname):
        # TODO: This function is incomplete and untested
        if macroname.startswith('$_SERVICE'):
            # If this is a custom macro
            name = macroname[9:-1]
            return self["_%s" % name]
        if _standard_macros.has_key( macroname ):
            attr = _standard_macros[ macroname ]
            return self[ attr ]
        return ''

    def _get_host_macro(self, macroname, host_name=None):
        # TODO: This function is incomplete and untested
        if macroname.startswith('$_HOST'):
            # if this is a custom macro
            name = macroname[6:-1]
            return self["_%s" % name]
        if _standard_macros.has_key( macroname ):
            attr = _standard_macros[ macroname ]
            return self[ attr ]
        return ''

    def get_effective_children(self, recursive=False):
        """ Get a list of all objects that inherit this object via "use" attribute
        
        Arguments:
            recursive - If true, include grandchildren as well
        Returns:
            A list of ObjectDefinition objects
        """
        if not self.has_key('name'):
            return []
        name = self['name']
        children = self.objects.filter(use__has_field=name)
        if recursive == True:
            grandchildren = []
            for i in children:
                grandchildren += i.get_effective_children(recursive)
            children += grandchildren
        return children

    def get_effective_parents(self, recursive=False):
        """ Get all objects that this one inherits via "use" attribute
        
        Arguments:
            recursive - If true include grandparents in list to be returned
        Returns:
            a list of ObjectDefinition objects
        """
        # TODO: This function is incomplete and untested
        if not self.has_key('use'):
            return []
        results = []
        use = self['use'].split(',')
        for parent_name in use:
            results.append( self.objects.get_by_name(parent_name) )
        if recursive is True:
            grandparents = []
            for i in results:
                grandparents.append( i.get_effective_parents(recursive=True))
            results += grandparents
        return results

    def get_attribute_tuple(self):
        """ Returns all relevant attributes in the form of:
        
        (attribute_name,defined_value,inherited_value)
        """
        result = []
        for k in self.keys():
            inher = defin = None 
            if self._inherited_attributes.has_key(k):
                inher = self._inherited_attributes[k]
            if self._defined_attributes.has_key(k):
                defin = self._defined_attributes[k]
            result.append((k, defin, inher))
        return result

    def get_parents(self):
        """Returns an ObjectDefinition list of all parents (via use attribute)"""
        result = []
        if not self['use']: return result
        for parent_name in self['use'].split(','):
            search = self.objects.filter(name=parent_name)
            if len(search) < 1: continue
            result.append(search[0])
        return result

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
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins,localadmins
            }
           >>> myservice.attribute_addfield(attribute_name="contactgroups", value='webmasters')
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins,localadmins,webmasters
            }
           """
        aList = AttributeList( self[attribute_name] )
        
        if value not in aList.fields:
            aList.fields.append( value )
            self[attribute_name] = str(aList)
        return

    def attribute_removefield(self, attribute_name, value):
        """Convenient way to remove value to an attribute with a comma seperated value

        Example:
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins,localadmins
            }
           >>> myservice.attribute_removefield(attribute_name="contactgroups", value='localadmins')
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins
            }
           """
        aList = AttributeList(self[attribute_name])

        if value in aList.fields:
            aList.fields.remove(value)
            self[attribute_name] = str(aList)
        return

    def attribute_replacefield(self, attribute_name, old_value, new_value):
        """Convenient way to replace field within an attribute with a comma seperated value

        Example:
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins,localadmins
            }
           >>> myservice.attribute_replacefield(attribute_name="contactgroups", old_value='localadmins', new_value=webmasters)
           >>> print myservice
           define service {
                ...
                contactgroups +alladmins,webmasters
            }
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
            result.append( tmp )
        if tmp is None or tmp.startswith('+'):
            for parent in self.get_parents():
                result.append( parent._get_effective_attribute(attribute_name) )
                if parent[attribute_name] is not None and not parent[attribute_name].startswith('+'):
                    break
        return_value = []
        for value in  result :
            value = value.strip('+')
            if value == '': continue
            if value not in return_value:
                return_value.append( value )
        tmp = ','.join( return_value )
        tmp = tmp.replace(',,',',')
        return tmp

    def _event(self, level=None, message=None):
        """ Pass informational message about something that has happened within the Model """
        for i in eventhandlers:
            if level == 'write':
                i.write( object_definition=self, message=message )
            elif level == 'save':
                i.save( object_definition=self, message=message )
            else:
                i.debug( object_definition=self, message=message )

    def _do_relations(self):
        """ Discover all related objects (f.e. services that belong to this host, etc

        ObjectDefinition only has relations via 'use' paramameter. Subclasses should extend this.
        """
        parents = AttributeList( self.use )
        for i in parents.fields:
            ObjectRelations.use[self.object_type][ i ].add( self.get_id() )


class Host(ObjectDefinition):
    object_type = 'host'
    objects = ObjectFetcher('host')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['host_name']

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this Host """
        get_object = lambda x: Service.objects.get_by_id(x)
        list_of_shortnames = ObjectRelations.host_services[self.host_name]
        return map( get_object, list_of_shortnames )

    def get_effective_contacts(self):
        """ Returns a list of all Contact that belong to this Host """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.host_contacts[self.host_name]
        return map( get_object, list_of_shortnames )

    def get_effective_contact_groups(self):
        """ Returns a list of all Contactgroup that belong to this Host """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.host_contact_groups[self.host_name]
        return map( get_object, list_of_shortnames )

    def get_effective_hostgroups(self):
        """ Returns a list of all Hostgroup that belong to this Host """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.host_hostgroups[self.host_name]
        return map( get_object, list_of_shortnames )

    def delete(self, recursive=False ):
        """ Overwrites objectdefinition so that recursive=True will delete all services as well """
        # Find all services and delete them as well
        if recursive == True:
            for i in self.get_effective_services():
                i.delete(recursive=recursive)
        # Call parent to get delete myself
        super(self.__class__, self).delete(recursive=recursive)

    def get_related_objects(self):
        result = super(self.__class__, self).get_related_objects()
        if self['host_name'] is not None:
            tmp = Service.objects.filter(host_name=self['host_name'])
            for i in tmp: result.append( i )
        return result

    def copy(self, recursive=False,filename=None, **args):
        """ Same as ObjectDefinition.copy() except can recursively copy services """
        new_object = ObjectDefinition.copy(self, recursive=recursive,filename=filename, **args)
        if recursive == True and 'host_name' in args:
            for i in self.get_effective_services():
                print i.get_shortname()
                i.copy(filename=filename, host_name=args.get('host_name'))
        return new_object

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        # Do hostgroups
        hg = AttributeList( self.hostgroups )
        for i in hg.fields:
            ObjectRelations.host_hostgroups[self.host_name].add( i )
            ObjectRelations.hostgroup_hosts[i].add( self.host_name )
        # Contactgroups
        cg = AttributeList( self.contact_groups )
        for i in cg.fields:
            ObjectRelations.host_contact_groups[self.host_name].add( i )
            ObjectRelations.contactgroup_hosts[i].add( self.host_name )
        contacts = AttributeList( self.contacts )
        for i in contacts.fields:
            ObjectRelations.host_contacts[self.host_name].add( i )
            ObjectRelations.contact_hosts[i].add( self.host_name )
        if self.check_command:
            command_name = self.check_command.split('!')[0]
            ObjectRelations.command_service[ self.host_name ].add( command_name )


class Service(ObjectDefinition):
    object_type = 'service'
    objects = ObjectFetcher('service')

    def get_description(self):
        """ Returns a friendly description of the object """
        return "%s/%s" % (self['host_name'], self['service_description'])

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
        hg = AttributeList( self.hostgroup_name )
        for i in hg.fields:
            ObjectRelations.service_hostgroups[self.get_id()].add( i )
            ObjectRelations.hostgroup_services[i].add( self.get_id() )
            # Contactgroups
        cg = AttributeList( self.contact_groups )
        for i in cg.fields:
            ObjectRelations.service_contact_groups[self.get_id()].add( i )
            ObjectRelations.contactgroup_services[i].add( self.get_id() )
        contacts = AttributeList( self.contacts )
        for i in contacts.fields:
            ObjectRelations.service_contacts[self.get_id()].add( i )
            ObjectRelations.contact_services[i].add( self.get_id() )
        sg = AttributeList( self.servicegroups )
        for i in sg.fields:
            ObjectRelations.service_servicegroups[self.get_id()].add( i )
            ObjectRelations.servicegroup_services[i].add( self.get_id() )
        if self.check_command:
            command_name = self.check_command.split('!')[0]
            ObjectRelations.command_service[ self.get_id() ].add( command_name )
        hosts = AttributeList( self.host_name )
        for i in hosts.fields:
            ObjectRelations.service_hosts[ self.get_id() ].add( i )
            ObjectRelations.host_services[ i ].add( self.get_id() )

    def get_effective_hosts(self):
        """ Returns a list of all Host that belong to this Service """
        get_object = lambda x: Host.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.service_hosts[ self.get_id() ]
        return map( get_object, list_of_shortnames )

    def get_effective_contacts(self):
        """ Returns a list of all Contact that belong to this Service """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.service_contacts[self.get_id()]
        return map( get_object, list_of_shortnames )

    def get_effective_contact_groups(self):
        """ Returns a list of all Contactgroup that belong to this Service """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.service_contact_groups[self.get_id()]
        return map( get_object, list_of_shortnames )

    def get_effective_hostgroups(self):
        """ Returns a list of all Hostgroup that belong to this Service """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.service_hostgroups[self.get_id()]
        return map( get_object, list_of_shortnames )

    def get_effective_servicegroups(self):
        """ Returns a list of all Servicegroup that belong to this Service """
        get_object = lambda x: Servicegroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.service_servicegroups[self.get_id()]
        return map( get_object, list_of_shortnames )

class Command(ObjectDefinition):
    object_type = 'command'
    objects = ObjectFetcher('command')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['command_name']


class Contact(ObjectDefinition):
    object_type = 'contact'
    objects = ObjectFetcher('contact')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['contact_name']

    def get_effective_contactgroups(self):
        """ Get a list of all Contactgroup that are hooked to this contact """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.contact_contactgroups[self.contact_name]
        return map( get_object, list_of_shortnames )

    def get_effective_hosts(self):
        """ Get a list of all Host that are hooked to this Contact """
        result = set()
        # First add all hosts that name this contact specifically
        get_object = lambda x: Host.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.contact_hosts[self.contact_name]
        result.update( map( get_object, list_of_shortnames ) )

        # Next do the same for all contactgroups this contact belongs in
        for i in self.get_effective_contactgroups():
            result.update( i.get_effective_hosts() )
        return result

    def get_effective_services(self):
        """ Get a list of all Service that are hooked to this Contact """
        result = set()
        # First add all services that name this contact specifically
        get_object = lambda x: Service.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.contact_services[self.contact_name]
        result.update( map( get_object, list_of_shortnames ) )
        return result

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        groups = AttributeList( self.contactgroups )
        for i in groups.fields:
            ObjectRelations.contact_contactgroups[self.contact_name].add( i )
            ObjectRelations.contactgroup_contacts[i].add( self.contact_name )


class ServiceDependency(ObjectDefinition):
    object_type = 'servicedependency'
    objects = ObjectFetcher('servicedependency')


class HostDependency(ObjectDefinition):
    object_type = 'hostdependency'
    objects = ObjectFetcher('hostdependency')


class Contactgroup(ObjectDefinition):
    object_type = 'contactgroup'
    objects = ObjectFetcher('contactgroup')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['contactgroup_name']

    def get_effective_contactgroups(self):
        """ Returns a list of every Contactgroup that is a member of this Contactgroup """
        get_object = lambda x: Contactgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.contactgroup_subgroups
        return map( get_object, list_of_shortnames )

    def get_effective_contacts(self):
        """ Returns a list of every Contact that is a member of this Contactgroup """
        get_object = lambda x: Contact.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.contactgroup_contact[self.contactgroup_name]
        return map( get_object, list_of_shortnames )

    def get_effective_hosts(self):
        """ Return every Host that belongs to this contactgroup """
        list_of_shortnames = ObjectRelations.contactgroup_hosts[self.contactgroup_name]
        get_object = lambda x: Host.objects.get_by_shortname(x)
        return map( get_object, list_of_shortnames )

    def get_effective_services(self):
        """ Return every Host that belongs to this contactgroup """
        services = {}
        for i in Service.objects.all:
            services[i.get_id()] = i
        list_of_shortnames = ObjectRelations.contactgroup_services[self.contactgroup_name]
        get_object = lambda x: services[x]
        return map( get_object, list_of_shortnames )

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        members = AttributeList( self.members )
        for i in members.fields:
            ObjectRelations.contactgroup_contacts[self.contactgroup_name].add( i )
            ObjectRelations.contact_contactgroups[i].add( self.contactgroup_name )
        groups = AttributeList( self.contactgroup_members )
        for i in groups.fields:
            ObjectRelations.contactgroup_contactgroups[self.contactgroup_name].add( i )

   
class Hostgroup(ObjectDefinition):
    object_type = 'hostgroup'
    objects = ObjectFetcher('hostgroup')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['hostgroup_name']

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this hostgroup """
        list_of_shortnames = ObjectRelations.hostgroup_services[self.hostgroup_name]
        get_object = lambda x: Service.objects.get_by_id(x)
        return map( get_object, list_of_shortnames )

    def get_effective_hosts(self):
        """ Returns a list of all Host that belong to this hostgroup """
        list_of_shortnames = ObjectRelations.hostgroup_hosts[self.hostgroup_name]
        get_object = lambda x: Host.objects.get_by_shortname(x)
        return map( get_object, list_of_shortnames )

    def get_effective_hostgroups(self):
        """ Returns a list of every Hostgroup that is a member of this Hostgroup """
        get_object = lambda x: Hostgroup.objects.get_by_shortname(x)
        list_of_shortnames = ObjectRelations.hostgroup_subgroups
        return map( get_object, list_of_shortnames )

    def _do_relations(self):
        super(self.__class__, self)._do_relations()
        members = AttributeList( self.members )
        for i in members.fields:
            ObjectRelations.hostgroup_hosts[self.hostgroup_name].add( i )
            ObjectRelations.host_hostgroups[i].add( self.hostgroup_name )
        groups = AttributeList( self.hostgroup_members )
        for i in groups.fields:
            ObjectRelations.hostgroup_hostgroups[self.hostgroup_name].add( i )


class Servicegroup(ObjectDefinition):
    object_type = 'servicegroup'
    objects = ObjectFetcher('servicegroup')

    def get_effective_services(self):
        """ Returns a list of all Service that belong to this Servicegroup """
        list_of_shortnames = ObjectRelations.servicegroup_services[self.servicegroup_name]
        get_object = lambda x: Service.objects.get_by_id(x)
        return map( get_object, list_of_shortnames )
    def get_description(self):
        """ Returns a friendly description of the object """
        return self['servicegroup_name']


class Timeperiod(ObjectDefinition):
    object_type = 'timeperiod'
    objects = ObjectFetcher('timeperiod')

    def get_description(self):
        """ Returns a friendly description of the object """
        return self['timeperiod_name']


class AttributeList(object):
    """ Parse a list of nagios attributes (e. contact_groups) into a parsable format

    This makes it handy to mangle with nagios attribute values that are in a comma seperated format.

    Typical comma-seperated format in nagios configuration files looks something like this:
        contact_groups     +group1,group2,group3

    Example:
        >>> i = AttributeList('+group1,group2,group3')
        >>> print "Operator is:", i.operator
        Operator is: +
        >>> print i.values
        ['group1','group2','group3']
    """

    def __init__(self, value=None):
        self.operator = ''
        self.fields = []
        
        # this is easy to do if attribue_name is unset
        if not value or value == '':
            return
    
        possible_operators = '+-!'
        if value[0] in possible_operators:
            self.operator = value[0]
        else:
            self.operator = ''
        
        self.fields = value.strip(possible_operators).split(',')

    def __str__(self):
        return self.operator + ','.join(self.fields)

    def __repr__(self):
        return self.__str__()

    def insert(self, index, object):
        return self.fields.insert(index,object) 

    def append(self, object):
        return self.fields.append(object)

    def count(self, value):
        return self.fields.count(value)

    def extend(self, iterable):
        return self.fields.extend(iterable)

    def index(self, value, start, stop):
        return self.fields.index(value, start, stop)

    def reverse(self):
        return self.fields.reverse()

    def sort(self):
        return self.fields.sort()

    def remove(self, value):
        return self.fields.remove(value)

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


if __name__ == '__main__':
    #s = Service.objects.all
    pass