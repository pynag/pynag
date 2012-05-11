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
from google.protobuf.internal.decoder import StringDecoder


"""
This module provides a high level Object-Oriented wrapper around pynag.Parsers.config.

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

__author__ = "Pall Sigurdsson"
__copyright__ = "Copyright 2011, Pall Sigurdsson"
__credits__ = ["Pall Sigurdsson"]
__license__ = "GPLv2"
__version__ = "0.4.1"
__maintainer__ = "Pall Sigurdsson"
__email__ = "palli@opensource.is"
__status__ = "Development"


import sys
import os
import re
from pynag import Parsers
from macros import _standard_macros


import time


# Path To Nagios configuration file
cfg_file = '/etc/nagios/nagios.cfg'
pynag_directory = '/etc/nagios/pynag/' # Were new objects are written by default
config = None
# TODO: Make this a lazy load, so config is only parsed when it needs to be.
#config = Parsers.config(cfg_file)
#config.parse()


#: eventhandlers -- A list of Model.EventHandelers object.
# Event handler is responsible for passing notification whenever something important happens in the model
# For example FileLogger class is an event handler responsible for logging to file whenever something has been written.
eventhandlers = []

def debug(text):
    if debug: print text



def contains(str1, str2):
    'Returns True if str1 contains str2'
    if str1.find(str2) > -1: return True

def not_contains(str1, str2):
    'Returns True if str1 does not contain str2'
    return not contains(str1, str2)

def has_field(str1, str2):
    '''Returns True if str2 is a field in str1
    
    For this purpose the string 'example' is a field in '+this,is,an,example'
    '''
    str1 = str1.strip('+')
    str1 = str1.split(',')
    if str2 in str1: return True
    return False
class ObjectFetcher(object):
    '''
    This class is a wrapper around pynag.Parsers.config. Is responsible for fetching dict objects
    from config.data and turning into high ObjectDefinition objects
    '''
    relations = {}
    def __init__(self, object_type):
        self.object_type = object_type
        self.objects = []
    def get_all(self):
        " Return all object definitions of specified type"
        if self.objects == []:
            'we get here on first run'
            self.reload_cache()
        elif config is None or config.needs_reparse():
            'We get here if any configuration file has changed'
            self.reload_cache()
        return self.objects
    all = property(get_all)
    def clean_cache(self):
        'Empties current object cache'
        debug("Debug: clean_cache()")
        global config
        config = None
        ObjectDefinition.objects.objects = []
    def reload_cache(self):
        'Reload configuration cache'
        debug('debug: reload_cache()')
        self.objects = []
        ObjectFetcher.relations= {}
        global config
        config = Parsers.config(cfg_file)
        config.parse()
        if self.object_type is not None:
            key_name = "all_%s" % (self.object_type)
            if not config.data.has_key(key_name):
                return []
            objects = config.data[ key_name ]
        else:
            # If no object type was requested
            objects = []
            for v in config.data.values():
                objects += v
        for i in objects:
            object_type = i['meta']['object_type']
            Class = string_to_class.get( object_type, ObjectDefinition )
            i = Class(item=i)
            #    self.find_relations(i)
            self.objects.append(i)
        return self.objects
    def get_by_id(self, id):
        ''' Get one specific object
        
        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        '''
        id = str(id)
        for item in self.all:
            if str(item['id']) == id:
                return item
        raise ValueError('No object with ID=%s found'% (id))
    def get_by_shortname(self, shortname):
        ''' Get one specific object by its shortname (i.e. host_name for host, etc)
        
        Returns:
            ObjectDefinition
        Raises:
            ValueError if object is not found
        '''
        attribute_name = "%s_name" % (self.object_type)
        for item in self.all:
            if item[attribute_name] == shortname:
                return item
        raise ValueError('No %s with %s=%s found' % (self.object_type, attribute_name,shortname))
    def get_object_types(self):
        ''' Returns a list of all discovered object types '''
        if config is None: self.reload_cache()
        return config.get_object_types()
    def filter(self, **kwargs):
        '''
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
        '''
        # TODO: Better testing of these cases:
        # register = 1
        # id attribute
        # any attribute = None or 'None'
        result = []
        # Lets convert all values to str()
        tmp = {}
        for k,v in kwargs.items():
            k = str(k)
            if v != None: v = str(v)
            tmp[k] = v
        kwargs = tmp
        for i in self.all:
            object_matches = True
            for k, v in kwargs.items():
                if k == ('exists'):
                    raise NotImplementedError('Dont use this. Doesnt work.')
                    v = k[:-8]
                    k = i
                    match_function = dict.has_key
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
                    'not defined means item is registered'
                    continue
                if v == None and i.has_key(k):
                    object_matches = False
                    break
                if not i.has_key(k):
                    if v == None: continue # if None was the search attribute
                    object_matches = False
                    break
                if not match_function(i[k], v):
                    object_matches = False
                    break
            if object_matches:
                result.append(i)
        return result        

    
class ObjectDefinition(object):
    '''
    Holds one instance of one particular Object definition
    Example usage:
        objects = ObjectDefinition.objects.all
        my_object ObjectDefinition( dict ) # dict = hash map of configuration attributes
    '''
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
        # Lets create dynamic convenience properties for each item
        for k in self._original_attributes.keys():
            if k == 'meta': continue
            self._add_property(k)
    
    def _add_property(self, name):
        ''' Creates dynamic properties for every attribute of out definition.
        
        i.e. this makes sure host_name attribute is accessable as self.host_name
        
        Returns: None
        '''
        fget = lambda self: self.get_attribute(name)
        fset = lambda self, value: self.set_attribute(name, value)
        setattr( self.__class__, name, property(fget,fset))
    def get_attribute(self, attribute_name):
        'Get one attribute from our object definition'
        return self[attribute_name]
    def set_attribute(self, attribute_name, attribute_value):
        'Set (but does not save) one attribute in our object'
        self[attribute_name] = attribute_value
        self._event(level="debug", message="attribute changed: %s = %s" % (attribute_name, attribute_value))
    def is_dirty(self):
        "Returns true if any attributes has been changed on this object, and therefore it needs saving"
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
        #return self.__str__().__hash__()
        object_type = self['object_type']
        shortname = self.get_description()
        object_name = self['name']
        filename = self['filename']
        object_id = "%s-%s-%s-%s" % ( object_type, shortname, object_name, filename)
        import md5
        return md5.new(id).hexdigest()
        return object_id
    def get_suggested_filename(self):
        "Returns a suitable configuration filename to store this object in"
        path = "" # End result will be something like '/etc/nagios/pynag/templates/hosts.cfg'
        object_type = self.object_type
        shortname = self.get_shortname()
        if self['register'] == "0":
            'This is a template'
            path = "%s/templates/%ss.cfg" % (pynag_directory, object_type)
        else:
            'Not a template'
            if object_type == 'service':
                'Services written in same file as their host'
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
        if self.is_new is True or self._meta['filename'] is None:
            if not self._meta['filename']:
                'discover a new filename'
                self._meta['filename'] = self.get_suggested_filename()
            for k,v in self._changes.items():
                self._defined_attributes[k] = v
                self._original_attributes[k] = v
                del self._changes[k]
            config.item_add(self._original_attributes, self._meta['filename'])
            return
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
                raise Exception("Failure saving object. filename=%s, object=%s" % (self['meta']['filename'], self['shortname']) )
        self.objects.clean_cache()

        # this piece of code makes sure that when we current object contains all current info
        new_me = self.objects.get_by_id(self.get_id())
        self._defined_attributes = new_me._defined_attributes
        self._original_attributes = new_me._original_attributes
        self._inherited_attributes = new_me._inherited_attributes
        self._meta = new_me._meta

        self._event(level='write', message="Object %s changed in file %s" % (self['shortname'], self['meta']['filename']))
        return number_of_changes
    def rewrite(self, str_new_definition=None):
        """ Rewrites this Object Definition in its configuration files.
        
        Arguments:
            str_new_definition = the actual string that will be written in the configuration file
            if str_new_definition is None, then we will use self.__str__()
        Returns: 
            True on success
        """
        if str_new_definition == None:
            str_new_definition = self['meta']['raw_definition']
        config.item_rewrite(self._original_attributes, str_new_definition)
        self['meta']['raw_definition'] = str_new_definition
        self._event(level='write', message="Object definition rewritten")
        return True
    def delete(self, cascade=False):
        """ Deletes this object definition from its configuration files.
        
        Arguments:
            Cascade: If True, look for items that depend on this object and delete them as well
            (for example, if you delete a host, delete all its services as well)
        """
        if cascade == True:
            raise NotImplementedError()
        else:
            result = config.item_remove(self._original_attributes)
            self._event(level="write", message="Object was deleted")
            return result
    def copy(self, filename=None, **args):
        """ Copies this object definition with any unsaved changes to a new configuration object
        
        Arguments:
          filename: If specified, new object will be saved in this file.
          **args: Any argument will be treated a modified attribute in the new definition.
        Examples:
          myhost = Host.objects.get_by_shortname('myhost.example.com')
          myhost.copy( host_name="newhost.example.com", address="127.0.0.1")
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
        print new_object
        new_object.save()
        
    def get_related_objects(self):
        """ Returns a list of ObjectDefinition that depend on this object
        
        Object can "depend" on another by a 'use' or 'host_name' or similar attribute
        
        Returns:
            List of ObjectDefinition objects
        """
        result = []
        if self['name'] != None:
            tmp = ObjectDefinition.objects.filter(use__has_field=self['name'], object_type=self['object_type'])
            for i in tmp: result.append(i)
        return result
    def __str__(self):
        return_buffer = "define %s {\n" % (self.object_type)
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
            return_buffer = return_buffer + "  %-30s %s\n" % (key, value)
        return_buffer = return_buffer + "}\n"
        return return_buffer
    def __repr__(self):
        return "%s: %s" % (self['object_type'], self.get_shortname())
        result = ""
        result += "%s: " % self.__class__.__name__
        for i in  ['object_type', 'host_name', 'name', 'use', 'service_description']:
            if self.has_key(i):
                result += " %s=%s " % (i, self[i])
            else:
                result += "%s=None " % (i)
        return result
    def get(self, value, default=None):
        ''' self.get(x) == self[x] '''
        if self.has_key(value): return self[value]
        return default
    def get_description(self):
        return self.get("%s_name" % self.object_type, None)
    def get_shortname(self):
        return self.get_description()
    def get_filename(self):
        """ Get name of the config file which defines this object
        """
        return self._meta['filename']
    def set_filename(self, filename):
        """ set name of the config file which defines this object"""
        self._meta['filename'] = filename
    def get_macro(self, macroname, host_name=None ):
        # TODO: This function is incomplete and untested
        if macroname.startswith('$ARG'):
            'Command macros handled in a special function'
            return self._get_command_macro(macroname)
        if macroname.startswith('$USER'):
            '$USERx$ macros are supposed to be private, but we will display them anyway'
            for mac,val in config.resource_values:
                if macroname == mac:
                    return val
            return ''
        if macroname.startswith('$HOST') or macroname.startswith('$_HOST'):
            return self._get_host_macro(macroname, host_name=host_name)
        if macroname.startswith('$SERVICE') or macroname.startswith('$_SERVICE'):
            return self._get_service_macro(macroname)
        if _standard_macros.has_key( macroname ):
            attr = _standard_macros[ macroname ]
            return self[ attr ]
        return ''
    def get_all_macros(self):
        "Returns {macroname:macrovalue} hash map of this object's macros"
        # TODO: This function is incomplete and untested
        if self['check_command'] == None: return None
        c = self['check_command']
        c = c.split('!')
        command_name = c.pop(0)
        command = Command.objects.get_by_shortname(command_name)
        regex = re.compile("(\$\w+\$)")
        macronames = regex.findall( command['command_line'] )
        result = {}
        for i in macronames:
            result[i] = self.get_macro(i)
        return result
    def get_effective_command_line(self, host_name=None):
        "Return a string of this objects check_command with all macros (i.e. $HOSTADDR$) resolved"
        # TODO: This function is incomplete and untested
        if self['check_command'] == None: return None
        c = self['check_command']
        c = c.split('!')
        command_name = c.pop(0)
        try:
            command = Command.objects.get_by_shortname(command_name)
        except ValueError:
            return None
        regex = re.compile("(\$\w+\$)")
        get_macro = lambda x: self.get_macro(x.group(), host_name=host_name)
        result = regex.sub(get_macro, command['command_line'])
        return result
    def _get_command_macro(self, macroname):
        "Resolve any command argument ($ARG1$) macros from check_command"
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
        if a.has_key( macroname ):
            return a[ macroname ]
        else:
            return '' # Return empty string if macro is invalid.
    def _get_service_macro(self,macroname):
        # TODO: This function is incomplete and untested
        if macroname.startswith('$_SERVICE'):
            'If this is a custom macro'
            name = macroname[9:-1]
            return self["_%s" % name]
        if _standard_macros.has_key( macroname ):
            attr = _standard_macros[ macroname ]
            return self[ attr ]
        return ''
    def _get_host_macro(self, macroname, host_name=None):
        # TODO: This function is incomplete and untested
        if macroname.startswith('$_HOST'):
            'if this is a custom macro'
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
            results.append( self.objects.filter(name=parent_name)[0] )
        if recursive is True:
            grandparents = []
            for i in results:
                grandparents.append( i.get_effective_parents(recursive=True))
            results += grandparents
        return results
    def get_effective_hostgroups(self):
        """Get all hostgroups that this object belongs to (not just the ones it defines on its own
        
        How can a hostgroup be linked to this object:
            1) This object has hostgroups defined via "hostgroups" attribute
            2) This object inherits hostgroups attribute from a parent
            3) A hostgroup names this object via members attribute
            4) A hostgroup names another hostgroup via hostgroup_members attribute
            5) A hostgroup inherits (via use) from a hostgroup who names this host
        """
        # TODO: This function is incomplete and untested
        # TODO: Need error handling when object defines hostgroups but hostgroup does not exist
        result = []
        hostgroup_list = []
        # Case 1 and Case 2:
        tmp = self._get_effective_attribute('hostgroups')
        for i in tmp.split(','):
            if i == '': continue
            i = Hostgroup.objects.get_by_shortname(i)
            if not i in result: result.append(i)
        '''
        # Case 1
        if self.has_key('hostgroups'):
            grp = self['hostgroups']
            grp = grp.split(',')
            for i in grp:
                i = i.strip('+')
                i = Hostgroup.objects.get_by_shortname(i)
                if not i in result: result.append(i)
        # Case 2:
        if not self.has_key('hostgroups') or self['hostgroups'].startswith('+'):
            parents = self.get_effective_parents()
            for parent in parents:
                parent_results += parent.get_effective_hostgroups()
        '''
        # Case 3:
        if self.has_key('host_name'):
            # We will use hostgroup_list in case 4 and 5 as well
            hostgroup_list = Hostgroup.objects.filter(members__has_field=self['host_name'])
            for hg in hostgroup_list:
                    if hg not in result:
                        result.append( hg )
        # Case 4:    
        for hg in hostgroup_list:
            if not hg.has_key('hostgroup_name'): continue
            grp = Hostgroup.objects.filter(hostgroup_members__has_field=hg['hostgroup_name'])
            for i in grp:
                if i not in result:
                    result.append(i )
        # Case 5:
        for hg in hostgroup_list:
            if not hg.has_key('hostgroup_name'): continue
            grp = Hostgroup.objects.filter(use__has_field=hg['hostgroup_name'])
            for i in grp:
                if i not in result:
                    result.append(i )
        
        return result
    def get_effective_contactgroups(self):
        # TODO: This function is incomplete and untested
        raise NotImplementedError()
    def get_effective_hosts(self):
        # TODO: This function is incomplete and untested
        raise NotImplementedError()
    def invalidate_cache(self):
        """ Makes sure next time we call self.objects.all or self.objects.filter it will be read from file """
        #self.objects.objects = []
        return True
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
        "Returns an ObjectDefinition list of all parents (via use attribute)"
        result = []
        if not self['use']: return result
        for parent_name in self['use'].split(','):
            parent = self.objects.filter(name=parent_name)[0]
            result.append(parent)
        return result
    def get_effective_contact_groups(self):
        "Returns a list of all contactgroups that belong to this service"
        result = []
        contactgroups = self._get_effective_attribute('contact_groups')
        for c in contactgroups.split(','):
            if c == '': continue
            group = Contactgroup.objects.get_by_shortname(c)
            result.append( group )
        return result
    def get_effective_contacts(self):
        "Returns a list of all contacts that belong to this service"
        result = []
        contacts = self._get_effective_attribute('contacts')
        for c in contacts.split(','):
            if c == '': continue
            contact = Contact.objects.get_by_shortname(c)
            result.append( contact )
        return result
    def _get_effective_attribute(self, attribute_name):
        """This helper function returns specific attribute, from this object or its templates
        
        This is handy for fields that effectively are many_to_many values.
        for example, "contactroups +group1,group2,group3"
        
        Fields that are known to use this format are:
            contacts, contactgroups, hostgroups, servicegroups, members,contactgroup_members
        """
        result = []
        tmp = self[attribute_name]
        if tmp != None:
            result.append( tmp )
        if tmp == None or tmp.startswith('+'):
            for parent in self.get_parents():
                result.append( parent._get_effective_attribute(attribute_name) )
                if parent[attribute_name] != None and not parent[attribute_name].startswith('+'):
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
            
                
                    
                
        
        
class Host(ObjectDefinition):
    object_type = 'host'
    objects = ObjectFetcher('host')
    def get_description(self):
        """ Returns a friendly description of the object """
        return self['host_name']
    def get_effective_services(self):
        """ Returns a list of all services that belong to this Host """
        if self['host_name'] == None:
            return []
        result = []
        myname = self['host_name']
        # Find all services that define us via service.host_name directive
        for service in Service.objects.all:
            service_hostname = service['host_name'] or ""
            if myname in service_hostname.split(","):
                result.append( service )
        # Find all services that define us via our hostgroup
        for hostgroup in self.get_effective_hostgroups():
            for service in hostgroup.get_effective_services():
                if service not in result:
                    result.append(service)
        return result
    def get_related_objects(self):
        result = super(self.__class__, self).get_related_objects()
        if self['host_name'] != None:
            tmp = Service.objects.filter(host_name=self['host_name'])
            for i in tmp: result.append( i )
        return result
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
        except:
            return None
            
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
    def get_effective_contact_groups(self):
        "Contact uses contactgroups instead of contact_groups"
        return self.get_effective_contactgroups()
    def get_effective_contactgroups(self):
        ''' Get a list of all contactgroups that are hooked to this contact '''
        result = []
        contactgroups = self._get_effective_attribute('contactgroups')
        for c in contactgroups.split(','):
            if c == '': continue
            group = Contactgroup.objects.get_by_shortname(c)
            if group not in result: result.append( group )
        # Additionally, check for contactgroups that define this contact as a member
        if self['contact_name'] == None: return result
        
        for cgroup in Contactgroup.objects.filter( members__has_field=self['contact_name'] ):
            if cgroup not in result: result.append( cgroup )
        return result
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
    def get_effective_members(self):
        ''' Returns every single member that belongs to this contactgroup, no matter where they are defined '''
        result = []
        do_relations()
        myname = self.get_description()
        contactgroups_tocheck = [ myname ]
        contactgroups_alreadychecked = []
        while len( contactgroups_tocheck ) > 0:
            group = contactgroups_tocheck.pop(0)
            if group in contactgroups_alreadychecked: continue
            members = relations['contactgroup_member'][group]
            for i in members:
                if not i in result: result.append(i)
            # expand group
            tmp =relations['contactgroup_contactgroup'].get(group, [])
            contactgroups_tocheck += tmp
            contactgroups_alreadychecked.append( group )
        result2 = []
        for i in result: result2.append( Contact.objects.get_by_shortname(i) )
        return result2
   
class Hostgroup(ObjectDefinition):
    object_type = 'hostgroup'
    objects = ObjectFetcher('hostgroup')
    def get_description(self):
        """ Returns a friendly description of the object """
        return self['hostgroup_name']
    def get_effective_services(self):
        """ Returns a list of all Service that belong to this hostgroup """
        myname = self['hostgroup_name']
        if not myname: return []
        
        result = []
        for service in Service.objects.all:
            hostgroup_name = service['hostgroup_name'] or ""
            hostgroups = service['hostgroups'] or ""
            if myname in hostgroups.split(','):
                result.append( service )
            elif myname in hostgroup_name.split(","):
                result.append( service )
        return result
class Servicegroup(ObjectDefinition):
    object_type = 'servicegroup'
    objects = ObjectFetcher('servicegroup')
    def get_description(self):
        """ Returns a friendly description of the object """
        return self['servicegroup_name']
class Timeperiod(ObjectDefinition):
    object_type = 'timeperiod'
    objects = ObjectFetcher('timeperiod')
    def get_description(self):
        """ Returns a friendly description of the object """
        return self['timeperiod_name']

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



def _test_get_by_id():
    'Do a quick unit test of the ObjectDefinition.get_by_id'
    hosts = Host.objects.all
    for h in hosts:
        id = h.get_id()
        h2 = Host.objects.get_by_id(id)
        if h.get_id() != h2.get_id():
            return False
    return True
"""
How can a contact belong to a group:
1) contact.contact_name is mentioned in contactgroup.members
2) contactgroup.contactgroup_name is mentioned in contact.contactgroups
3) contact belongs to contactgroup.use
4) contact belongs to contactgroup.countactgroup.use
"""

relations = {
             'contactgroup_member':{},
             'member_contactgroup':{},
             'contactgroup_contactgroup':{},
             }

def add_contact_to_group(contact_name, contactgroup_name):
    global relations
    if not relations['contactgroup_member'].has_key(contactgroup_name):
        relations['contactgroup_member'][contactgroup_name] = []
    if not relations['member_contactgroup'].has_key(contact_name):
        relations['member_contactgroup'][contact_name] = []
    if not contact_name in relations['contactgroup_member'][contactgroup_name]:
        relations['contactgroup_member'][contactgroup_name].append(contact_name)
    if not contactgroup_name in relations['member_contactgroup'][contact_name]:
        relations['member_contactgroup'][contact_name].append(contactgroup_name)
    return True

def add_group_to_group(contactgroup1, contactgroup2):
    global relations
    group = relations['contactgroup_contactgroup'].get(contactgroup1, [])
    if not contactgroup2 in group:
        group.append(contactgroup2)
    relations['contactgroup_contactgroup'][contactgroup1] = group
    return True

def do_relations():        
    all_contactgroups = Contactgroup.objects.all
    all_contacts = Contact.objects.all
    
    for i in all_contactgroups: relations['contactgroup_member'][i.get_shortname()] = []
    for i in all_contacts: relations['member_contactgroup'][i.get_shortname()] = []
    # Case 1
    for group in all_contactgroups:
        relations['contactgroup_member'][group.get_shortname()]
        members = group._get_effective_attribute('members')
        contactgroup_members = group._get_effective_attribute('contactgroup_members')
        if members:
            members = members.split(',')
            for i in members: add_contact_to_group(i, group.get_shortname())
        if contactgroup_members:
            contactgroup_members = contactgroup_members.split(',')
            for i in contactgroup_members:
                add_group_to_group(group.get_shortname(), i)
    for contact in all_contacts:
        groups = contact._get_effective_attribute('contactgroups')
        if groups:
            groups = groups.split(',')
            for i in groups: add_contact_to_group(contact.get_shortname(), i)
    
if __name__ == '__main__':
    pass
