# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2010 Drew Stinnet
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

import os
import re
import time
import socket # for mk_livestatus

import pynag.Plugins
def debug(text):
    debug = True
    if debug: print text


class config:
    """
    Parse and write nagios config files
    """
    def __init__(self, cfg_file=None,strict=False):
        """

        Arguments:
          cfg_file -- Full path to nagios.cfg. If None, try to auto-discover location
          strict   -- if True, use stricter parsing which is more prone to raising exceptions
        """

        self.cfg_file = cfg_file  # Main configuration file
        self.strict = strict # Use strict parsing or not

        # If nagios.cfg is not set, lets do some minor autodiscover.
        if self.cfg_file is None:
            self.cfg_file = self.guess_cfg_file()
        self.data = {}
        self.maincfg_values = []

    def guess_cfg_file(self):
        """ Returns a path to any nagios.cfg found on your system

        Use this function if you don't want specify path to nagios.cfg in your
        code and you are confident that it is located in a common location
        """
        possible_files = ('/etc/nagios/nagios.cfg',
                          '/etc/nagios3/nagios.cfg',
                          '/usr/local/nagios/etc/nagios.cfg',
                          '/nagios/etc/nagios/nagios.cfg',
                          './nagios.cfg',
                          './nagios/nagios.cfg',
            )
        for file in possible_files:
            if os.path.isfile(file):
                return file
        raise ParserError('Could not find nagios.cfg')
    def reset(self):
        self.cfg_files = [] # List of other configuration files
        self.data = {} # dict of every known object definition
        self.errors = [] # List of ParserErrors
        self.item_list = None
        self.item_cache = None
        self.maincfg_values = [] # The contents of main nagios.cfg
        self._resource_values = [] # The contents of any resource_files

        ## This is a pure listof all the key/values in the config files.  It
        ## shouldn't be useful until the items in it are parsed through with the proper
        ## 'use' relationships
        self.pre_object_list = []
        self.post_object_list = []
        self.object_type_keys = {
            'hostgroup':'hostgroup_name',
            'hostextinfo':'host_name',
            'host':'host_name',
            'service':'name',
            'servicegroup':'servicegroup_name',
            'contact':'contact_name',
            'contactgroup':'contactgroup_name',
            'timeperiod':'timeperiod_name',
            'command':'command_name',
            #'service':['host_name','description'],
        }

    def _has_template(self, target):
        """
        Determine if an item has a template associated with it
        """
        return 'use' in target

    def _get_pid(self):
        """
        Checks the lock_file var in nagios.cfg and returns the pid from the file

        If the pid file does not exist, returns None.
        """
        try:
            return open(self.get_cfg_value('lock_file'), "r").readline().strip()
        except Exception:
            return None

    def _get_hostgroup(self, hostgroup_name):
        return self.data['all_hostgroup'].get(hostgroup_name, None)

    def _get_key(self, object_type, user_key = None):
        """
        Return the correct 'key' for an item.  This is mainly a helper method
        for other methods in this class.  It is used to shorten code repitition
        """
        if not user_key and not self.object_type_keys.has_key(object_type):
            raise ParserError("Unknown key for object type:  %s\n" % object_type)

        ## Use a default key
        if not user_key:
            user_key = self.object_type_keys[object_type]

        return user_key

    def _get_item(self, item_name, item_type):
        """ 
           Return an item from a list
           """
        # create local cache for performance optimizations. TODO: Rewrite functions that call this function
        if not self.item_list:
            self.item_list = self.pre_object_list
            self.item_cache = {}
            for item in self.item_list:
                if not item.has_key('name'):
                    continue
                name = item['name']
                tmp_item_type = (item['meta']['object_type'])
                if not self.item_cache.has_key(tmp_item_type):
                    self.item_cache[tmp_item_type] = {}
                self.item_cache[tmp_item_type][name] = item
        return self.item_cache[item_type].get(item_name, None)

    def _apply_template(self, original_item):
        """
        Apply all attributes of item named parent_name to "original_item".
        """
        # If item does not inherit from anyone else, lets just return item as is.
        if not original_item.has_key('use'):
            return original_item
        object_type = original_item['meta']['object_type']
        # Performance tweak, if item has been parsed. Lets not do it again
        if original_item.has_key('name') and self.item_apply_cache[object_type].has_key(original_item['name']):
            return self.item_apply_cache[object_type][ original_item['name'] ]
        # End of performance tweak
        parent_names = original_item['use'].split(',')
        parent_items = []
        for parent_name in parent_names:
            parent_item = self._get_item( parent_name, object_type )
            if parent_item is None:
                error_string = "Can not find any %s named %s\n" % (object_type,parent_name)
                self.errors.append( ParserError(error_string,item=original_item) )
                continue
            # Parent item probably has use flags on its own. So lets apply to parent first
            try:
                parent_item = self._apply_template( parent_item )
            except RuntimeError, e:
                self.errors.append( ParserError("Error while parsing item: %s (it might have circular use=)" % str(e), item=original_item) )
            parent_items.append( parent_item )
        for parent_item in parent_items:
            for k,v in parent_item.iteritems():
                if k == 'use':
                    continue
                if k == 'register':
                    continue
                if k == 'meta':
                    continue
                if k == 'name':
                    continue
                if not original_item['meta']['inherited_attributes'].has_key(k):
                    original_item['meta']['inherited_attributes'][k] = v
                if not original_item.has_key(k):
                    original_item[k] = v
                    original_item['meta']['template_fields'].append(k)
        if original_item.has_key('name'):
            self.item_apply_cache[object_type][ original_item['name'] ] = original_item
        return original_item

    def _get_items_in_file(self, filename):
        """
        Return all items in the given file
        """
        return_list = []

        for k in self.data.keys():
            for item in self[k]:
                if item['meta']['filename'] == filename:
                    return_list.append(item)
        return return_list

    def get_new_item(self, object_type, filename):
        """ Returns an empty item with all necessary metadata """
        current = {}
        current['meta'] = {}
        current['meta']['object_type'] = object_type
        current['meta']['filename'] = filename
        current['meta']['template_fields'] = []
        current['meta']['needs_commit'] = None
        current['meta']['delete_me'] = None
        current['meta']['defined_attributes'] = {}
        current['meta']['inherited_attributes'] = {}
        current['meta']['raw_definition'] = "define %s {\n\n}" % object_type
        return current

    def _load_file(self, filename):
        ## Set globals (This is stolen from the perl module)
        append = ""
        current = None
        in_definition = {}
        tmp_buffer = []

        for sequence_no, line in enumerate( open(filename, 'rb').readlines() ):
            line_num = sequence_no + 1

            ## Cleanup and line skips
            line = line.strip()
            if line == "":
                continue
            if line[0] == "#" or line[0] == ';':
                continue

            # TODO: Find out why this code append lives here, are there really any cases
            # Where a nagios attributes expands more than one line ? 
            # append saved text to the current line
            if append:
                append += ' '
                line = append + line
                append = None

            # end of object definition
            if line.find("}") != -1:

                in_definition = None
                current['meta']['line_end'] = line_num
                # Looks to me like nagios ignores everything after the } so why shouldn't we ?
                rest = line.split("}", 1)[1]
                
                tmp_buffer.append(  line )
                try:
                    current['meta']['raw_definition'] = '\n'.join( tmp_buffer )
                except Exception:
                    raise ParserError("Encountered Unexpected end of object definition in file '%s'." % filename)
                self.pre_object_list.append(current)

                ## Destroy the Nagios Object
                current = None
                continue

            # beginning of object definition
            boo_re = re.compile("^\s*define\s+(\w+)\s*\{?(.*)$")
            m = boo_re.search(line)
            if m:
                tmp_buffer = [line]
                object_type = m.groups()[0]
                if self.strict and object_type not in self.object_type_keys.keys():
                    raise ParserError("Don't know any object definition of type '%s'. it is not in a list of known object definitions." % object_type)
                current = self.get_new_item(object_type, filename)
                current['meta']['line_start'] = line_num

                if in_definition:
                    raise ParserError("Error: Unexpected start of object definition in file '%s' on line %d.  Make sure you close preceding objects before starting a new one." % (filename,line_num))

                ## Start off an object
                in_definition = True
                
                # Looks to me like nagios ignores everything after the {, so why shouldn't we ?
                rest = m.groups()[1]
                continue
            else:
                tmp_buffer.append( '    ' + line )

            ## save whatever's left in the buffer for the next iteration
            if not in_definition:
                append = line
                continue

            ## this is an attribute inside an object definition
            if in_definition:
                #(key, value) = line.split(None, 1)
                tmp = line.split(None, 1)
                if len(tmp) > 1:
                    (key, value) = tmp
                else:
                    key = tmp[0]
                    value = ""

                ## Strip out in-line comments
                if value.find(";") != -1:
                    value = value.split(";", 1)[0]

                ## Clean info
                key = key.strip()
                value = value.strip()

                ## Rename some old values that may be in the configuration
                ## This can probably be removed in the future to increase performance
                if (current['meta']['object_type'] == 'service') and key == 'description':
                    key = 'service_description'

                # Special hack for timeperiods as they are not consistent with other objects
                # We will treat whole line as a key with an empty value
                if (current['meta']['object_type'] == 'timeperiod' ) and key not in  ('timeperiod_name', 'alias'):
                    key = line
                    value = ''
                current[key] = value
                current['meta']['defined_attributes'][key] = value
            ## Something is wrong in the config
            else:
                raise ParserError("Error: Unexpected token in file '%s'" % filename)

        ## Something is wrong in the config
        if in_definition:
            raise ParserError("Error: Unexpected EOF in file '%s'" % filename)

    def _locate_item(self, item):
        """
        This is a helper function for anyone who wishes to modify objects. It takes "item", locates the
        file which is configured in, and locates exactly the lines which contain that definition.
        
        Returns tuple:
            (everything_before, object_definition, everything_after, filename)
            everything_before(string) - Every line in filename before object was defined
            everything_after(string) - Every line in "filename" after object was defined
            object_definition - exact configuration of the object as it appears in "filename"
            filename - file in which the object was written to
        Raises:
            ValueError if object was not found in "filename"
        """
        if item['meta'].has_key("filename"):
            filename = item['meta']['filename']
        else:
            raise ValueError("item does not have a filename")
        file = open(filename)
        object_has_been_found = False
        everything_before = [] # Every line before our object definition
        everything_after = []  # Every line after our object definition
        object_definition = [] # List of every line of our object definition
        tmp_buffer = []        # Every line of current object being parsed is stored here.
        current_object_type = None # Object type of current object goes in here
        i_am_within_definition = False
        for line in file.readlines():
            if object_has_been_found:
                # If we have found an object, lets just spool to the end
                everything_after.append( line )
                continue
            tmp = line.split(None, 1)
            if len(tmp) == 0:
                # empty line
                keyword = ''
                rest = ''
            elif len(tmp) == 1:
                # single word on the line
                keyword = tmp[0]
                rest = ''
            else:
                keyword, rest = tmp[0], tmp[1]
            keyword = keyword.strip()
            # If we reach a define statement, we log every line to a special buffer
            # When define closes, we parse the object and see if it is the object we
            # want to modify
            if keyword == 'define':
                current_object_type = rest.split(None,1)[0]
                current_object_type = current_object_type.strip(';')
                current_object_type = current_object_type.strip('{')
                current_object_type = current_object_type.strip()
                tmp_buffer = []
                i_am_within_definition = True
            if i_am_within_definition == True:
                tmp_buffer.append( line )
            else:
                everything_before.append( line )
            if len(keyword) > 0 and keyword[0] == '}':
                i_am_within_definition = False
                
                current_candidate = self.get_new_item(object_type=current_object_type, filename=filename)
                for i in tmp_buffer:
                    i = i.strip()
                    tmp = i.split(None, 1)
                    if len(tmp) == 0:
                        continue
                    # Hack that makes timeperiod attributes be contained only in the key
                    if current_object_type == 'timeperiod' and tmp[0] not in ('alias', 'timeperiod_name'):
                        k = i
                        v = ''
                    elif len(tmp) == 1:
                        k = tmp[0]
                        v = ''
                    elif len(tmp) > 1:
                        k,v = tmp[0],tmp[1]
                        v = v.split(';',1)[0]
                        v = v.strip()
                    else: continue # skip empty lines
                    
                    if k.startswith('#'): continue
                    if k.startswith(';'): continue
                    if k.startswith('define'): continue
                    if k.startswith('}'): continue
                    
                    current_candidate[k] = v
                    current_candidate['meta']['defined_attributes'][k] = v
                    # Apply template should not be needed anymore
                    #current_candidate = self._apply_template(current_candidate)
                # Compare objects
                if self.compareObjects( item, current_candidate ) == True:
                    # This is the object i am looking for
                    object_has_been_found = True
                    object_definition = tmp_buffer
                else:
                    # This is not the item you are looking for
                    everything_before += tmp_buffer
        if object_has_been_found:
            return everything_before, object_definition, everything_after, filename
        else:
            raise ValueError("We could not find object in %s\n%s" % (filename,item))

    def _modify_object(self, item, field_name=None, new_value=None, new_field_name=None, new_item=None, make_comments=True):
        """
        Helper function for object_* functions. Locates "item" and changes the line which contains field_name.
        If new_value and new_field_name are both None, the attribute is removed.

        Arguments:
            item(dict) -- The item to be modified
            field_name(str) -- The field_name to modify (if any)
            new_field_name(str) -- If set, field_name will be renamed
            new_value(str) -- If set the value of field_name will be changed
            new_item(str) -- If set, whole object will be replaced with this string
            make_comments -- If set, put pynag-branded comments where changes have been made
        Returns:
            True on success
        Raises:
            ValueError if object or field_name is not found
            IOError is save is unsuccessful.
        """
        if field_name is None and new_item is None:
            raise ValueError("either field_name or new_item must be set")
        everything_before,object_definition, everything_after, filename = self._locate_item(item)
        if new_item is not None:
            # We have instruction on how to write new object, so we dont need to parse it
            object_definition = [new_item]
        else:
            change = None
            i = 0
            for i in range( len(object_definition)):
                tmp = object_definition[i].split(None, 1)
                if len(tmp) == 0: continue
                # Hack for timeperiods, they dont work like other objects
                elif item['meta']['object_type'] == 'timeperiod' and field_name not in ('alias', 'timeperiod_name'):
                    tmp = [object_definition[i]]
                    # we can't change timeperiod, so we fake a field rename
                    if new_value is not None:
                        new_field_name = new_value
                        new_value = None
                        value = ''
                elif len(tmp) == 1: value = ''
                else: value = tmp[1]
                k = tmp[0].strip()
                if k == field_name:
                    # Attribute was found, lets change this line
                    if new_field_name is None and new_value is None:
                        # We take it that we are supposed to remove this attribute
                        change = object_definition.pop(i)
                        break
                    elif new_field_name:
                        # Field name has changed
                        k = new_field_name
                    if new_value is not None:
                        # value has changed
                        value = new_value
                    # Here we do the actual change    
                    change = "\t%-30s%s\n" % (k, value)
                    if item['meta']['object_type'] == 'timeperiod' and field_name not in ('alias', 'timeperiod_name'):
                        change = "\t%s\n" % (new_field_name)
                    object_definition[i] = change
                    break
            if not change and new_value is not None:
                # Attribute was not found. Lets add it
                change = "\t%-30s%s\n" % (field_name, new_value)
                object_definition.insert(i,change)
        # Lets put a banner in front of our item
        if make_comments:
            comment = '# Edited by PyNag on %s\n' % time.ctime()
            if len(everything_before) > 0:
                last_line_before = everything_before[-1]
                if last_line_before.startswith('# Edited by PyNag on'):
                    everything_before.pop() # remove this line
            object_definition.insert(0, comment)
        # Here we overwrite the config-file, hoping not to ruin anything
        buffer = "%s%s%s" % (''.join(everything_before), ''.join(object_definition), ''.join(everything_after))
        file = open(filename,'w')
        file.write( buffer )
        file.close()
        return True        

    def item_rewrite(self, item, str_new_item):
        """
        Completely rewrites item with string provided.
        
        Arguments:
            item -- Item that is to be rewritten
            str_new_item -- str representation of the new item
        Examples:
            item_rewrite( item, "define service {\n name example-service \n register 0 \n }\n" )
        Returns:
            True on success
        Raises:
            ValueError if object is not found
            IOError if save fails
        """
        return self._modify_object(item=item, new_item=str_new_item)

    def item_remove(self, item):
        """
        Completely rewrites item with string provided.
        
        Arguments:
            item -- Item that is to be rewritten
            str_new_item -- str representation of the new item
        Examples:
            item_rewrite( item, "define service {\n name example-service \n register 0 \n }\n" )
        Returns:
            True on success
        Raises:
            ValueError if object is not found
            IOError if save fails
        """
        return self._modify_object(item=item, new_item="")

    def item_edit_field(self, item, field_name, new_value):
        """
        Modifies one field of a (currently existing) object. Changes are immediate (i.e. there is no commit)
        
        Example usage:
            edit_object( item, field_name="host_name", new_value="examplehost.example.com")
        Returns:
            True on success
        Raises:
            ValueError if object is not found
            IOError if save fails
        """
        return self._modify_object(item, field_name=field_name, new_value=new_value)
    
    def item_remove_field(self, item, field_name):
        """
        Removes one field of a (currently existing) object. Changes are immediate (i.e. there is no commit)
        
        Example usage:
            item_remove_field( item, field_name="contactgroups" )
        Returns:
            True on success
        Raises:
            ValueError if object is not found
            IOError if save fails
        """
        return self._modify_object(item=item, field_name=field_name, new_value=None, new_field_name=None)
    
    def item_rename_field(self, item, old_field_name, new_field_name):
        """
        Renames a field of a (currently existing) item. Changes are immediate (i.e. there is no commit).
        
        Example usage:
            item_rename_field(item, old_field_name="normal_check_interval", new_field_name="check_interval")
        Returns:
            True on success
        Raises:
            ValueError if object is not found
            IOError if save fails
        """
        return self._modify_object(item=item, field_name=old_field_name, new_field_name=new_field_name)

    def item_add(self, item, filename):
        """
        Adds a new object to a specified config file
        
        Arguments:
            item -- Item to be created
            filename -- Filename that we are supposed to write to
        Returns:
            True on success
        Raises:
            IOError on failed save
        """
        if not 'meta' in item:
            item['meta'] = {}
        item['meta']['filename'] = filename
        
        # Create directory if it does not already exist                
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        buffer = self.print_conf( item )
        file = open(filename,'a')
        file.write( buffer )
        file.close()
        return True        
            
    def edit_object(self, item, field_name, new_value):
        """
        Modifies a (currently existing) item. Changes are immediate (i.e. there is no commit)
        
        Example Usage: edit_object( item, field_name="host_name", new_value="examplehost.example.com")
        
        THIS FUNCTION IS DEPRECATED. USE item_edit_field() instead
        """
        return self.item_edit_field(item=item, field_name=field_name, new_value=new_value)

    def compareObjects(self, item1, item2):
        """
        Compares two items. Returns true if they are equal"
        """
        keys1 = item1['meta']['defined_attributes'].keys()
        keys2 = item2['meta']['defined_attributes'].keys()
        keys1.sort()
        keys2.sort()
        result = True
        if keys1 != keys2:
            return False
        for key in keys1:
            if key == 'meta': continue
            key1 = item1[key]
            key2 = item2[key]
            # For our purpose, 30 is equal to 30.000
            if key == 'check_interval':
                key1 = int(float(key1))
                key2 = int(float(key2))
            if str(key1) != str(key2):
                result = False
        if result == False: return False
        return True

    def edit_service(self, target_host, service_description, field_name, new_value):
        """
        Edit a service's attributes
        """

        original_object = self.get_service(target_host, service_description)
        if original_object is None:
            raise ParserError("Service not found")
        return self.edit_object( original_object, field_name, new_value)

    def _get_list(self, object, key):
        """
        Return a comma list from an item

        Example:

        _get_list(Foo_object, host_name)
        define service {
            service_description Foo
            host_name            larry,curly,moe
        }

        return
        ['larry','curly','moe']
        """
        if type(object) != type({}):
            raise ParserError("%s is not a dictionary\n" % object)
            # return []
        if not object.has_key(key):
            return []

        return_list = []

        if object[key].find(",") != -1:
            for name in object[key].split(","):
                return_list.append(name)
        else:
            return_list.append(object[key])

        ## Alphabetize
        return_list.sort()

        return return_list
        
    def delete_object(self, object_type, object_name, user_key = None):
        """
        Delete object from configuration files.
        """
        object_key = self._get_key(object_type, user_key)

        k = 'all_%s' % object_type
        if k not in self.data: return None
        for item in self.data[k]:
            if not item.has_key(object_key):
                continue

            ## If the object matches, mark it for deletion
            if item[object_key] == object_name:
                self.data[k].remove(item)
                item['meta']['delete_me'] = True
                item['meta']['needs_commit'] = True
                self.data[k].append(item)

                ## Commit the delete
                self.commit()
                return True

        ## Only make it here if the object isn't found
        return None

    def delete_service(self, service_description, host_name):
        """
        Delete service from configuration
        """
        for item in self.data['all_service']:
            if ('service_description' in item and item['service_description'] == service_description) and (host_name in self._get_active_hosts(item)):
                self.data['all_service'].remove(item)
                item['meta']['delete_me'] = True
                item['meta']['needs_commit'] = True
                self.data['all_service'].append(item)

                return True

    def delete_host(self, object_name, user_key = None):
        """
        Delete a host
        """
        return self.delete_object('host', object_name, user_key = user_key)

    def delete_hostgroup(self, object_name, user_key = None):
        """
        Delete a hostgroup
        """
        return self.delete_object('hostgroup', object_name, user_key = user_key)

    def get_object(self, object_type, object_name, user_key = None):
        """
        Return a complete object dictionary
        """
        object_key = self._get_key(object_type, user_key)

        target_object = None

        #print object_type
        for item in self.data['all_%s' % object_type]:
            ## Skip items without the specified key
            if not item.has_key(object_key):
                continue
            if item[object_key] == object_name:
                target_object = item
            ## This is for multi-key items
        return target_object

    def get_host(self, object_name, user_key = None):
        """
        Return a host object
        """
        return self.get_object('host', object_name, user_key = user_key)

    def get_servicegroup(self, object_name, user_key = None):
        """
        Return a Servicegroup object
        """
        return self.get_object('servicegroup', object_name, user_key = user_key)

    def get_contact(self, object_name, user_key = None):
        """
        Return a Contact object
        """
        return self.get_object('contact', object_name, user_key = user_key)

    def get_contactgroup(self, object_name, user_key = None):
        """
        Return a Contactgroup object
        """
        return self.get_object('contactgroup', object_name, user_key = user_key)

    def get_timeperiod(self, object_name, user_key = None):
        """
        Return a Timeperiod object
        """
        return self.get_object('timeperiod', object_name, user_key = user_key)

    def get_command(self, object_name, user_key = None):
        """
        Return a Command object
        """
        return self.get_object('command', object_name, user_key = user_key)

    def get_hostgroup(self, object_name, user_key = None):
        """
        Return a hostgroup object
        """
        return self.get_object('hostgroup', object_name, user_key = user_key)

    def get_servicedependency(self, object_name, user_key = None):
        """
        Return a servicedependency object
        """
        return self.get_object('servicedependency', object_name, user_key = user_key)

    def get_hostdependency(self, object_name, user_key = None):
        """
        Return a hostdependency object
        """
        return self.get_object('hostdependency', object_name, user_key = user_key)

    def get_service(self, target_host, service_description):
        """
        Return a service object.  This has to be seperate from the 'get_object'
        method, because it requires more than one key
        """
        for item in self.data['all_service']:
            ## Skip service with no service_description
            if not item.has_key('service_description'):
                continue
            ## Skip non-matching services
            if item['service_description'] != service_description:
                continue

            if target_host in self._get_active_hosts(item):
                return item

        return None

    def _append_use(self, source_item, name):
        """ Append attributes to source_item that are inherited via 'use' attribute'

        Attributes:
          source_item  -- item (dict) to apply the inheritance upon
          name         -- obsolete (discovered automatically via source_item['use']. Here for compatibility.
        """
        ## Remove the 'use' key
        if source_item.has_key('use'):
            del source_item['use']
        
        for possible_item in self.pre_object_list:
            if possible_item.has_key('name'):
                ## Start appending to the item
                for k,v in possible_item.iteritems():

                    try:
                        if k == 'use':
                            source_item = self._append_use(source_item, v)
                    except Exception:
                        raise ParserError( "Recursion error on %s %s" % (source_item, v) )

                    ## Only add the item if it doesn't already exist
                    if not source_item.has_key(k):
                        source_item[k] = v
        return source_item

    def _post_parse(self):
        self.item_list = None
        self.item_apply_cache = {} # This is performance tweak used by _apply_template
        for raw_item in self.pre_object_list:
            # Performance tweak, make sure hashmap exists for this object_type
            object_type = raw_item['meta']['object_type']
            if not self.item_apply_cache.has_key( object_type ):
                self.item_apply_cache[ object_type ] = {}
            # Tweak ends
            if raw_item.has_key('use'):
                raw_item = self._apply_template( raw_item )
            self.post_object_list.append(raw_item)
        ## Add the items to the class lists.  
        for list_item in self.post_object_list:
            type_list_name = "all_%s" % list_item['meta']['object_type']
            if not self.data.has_key(type_list_name):
                self.data[type_list_name] = []

            self.data[type_list_name].append(list_item)

    def commit(self):
        """
        Write any changes that have been made to it's appropriate file
        """
        ## Loops through ALL items
        for k in self.data.keys():
            for item in self[k]:

                ## If the object needs committing, commit it!
                if item['meta']['needs_commit']:
                    ## Create file contents as an empty string
                    file_contents = ""

                    ## find any other items that may share this config file
                    extra_items = self._get_items_in_file(item['meta']['filename'])
                    if len(extra_items) > 0:
                        for commit_item in extra_items:
                            ## Ignore files that are already set to be deleted:w
                            if commit_item['meta']['delete_me']:
                                continue
                            ## Make sure we aren't adding this thing twice
                            if item != commit_item:
                                file_contents += self.print_conf(commit_item)

                    ## This is the actual item that needs commiting
                    if not item['meta']['delete_me']:
                        file_contents += self.print_conf(item)

                    ## Write the file
                    f = open(item['meta']['filename'], 'w')
                    f.write(file_contents)
                    f.close()

                    ## Recreate the item entry without the commit flag
                    self.data[k].remove(item)
                    item['meta']['needs_commit'] = None
                    self.data[k].append(item)

    def flag_all_commit(self):
        """
        Flag every item in the configuration to be committed
        This should probably only be used for debugging purposes
        """
        for object_type in self.data.keys():
            for item in self.data[object_type]:
                item['meta']['needs_commit'] = True

    def print_conf(self, item):
        """
        Return a string that can be used in a configuration file
        """
        output = ""
        ## Header, to go on all files
        output += "# Configuration file %s\n" % item['meta']['filename']
        output += "# Edited by PyNag on %s\n" % time.ctime()

        ## Some hostgroup information
        if item['meta'].has_key('hostgroup_list'):
            output += "# Hostgroups: %s\n" % ",".join(item['meta']['hostgroup_list'])

        ## Some hostgroup information
        if item['meta'].has_key('service_list'):
            output += "# Services: %s\n" % ",".join(item['meta']['service_list'])

        ## Some hostgroup information
        if item['meta'].has_key('service_members'):
            output += "# Service Members: %s\n" % ",".join(item['meta']['service_members'])

        if len(item['meta']['template_fields']) != 0:
            output += "# Values from templates:\n"
        for k in item['meta']['template_fields']:
            output += "#\t %-30s %-30s\n" % (k, item[k])
        output += "\n"
        output += "define %s {\n" % item['meta']['object_type']
        for k, v in item.iteritems():
            if v is None:
                # Skip entries with No value
                continue
            if k != 'meta':
                if k not in item['meta']['template_fields']:
                    output += "\t %-30s %-30s\n" % (k,v)
        
        output += "}\n\n"
        return output

    def _load_static_file(self, filename=None):
        """Load a general config file (like nagios.cfg) that has key=value config file format. Ignore comments

        Arguments:
          filename -- name of file to parse, if none nagios.cfg will be used

        Returns:
            a [ (key,value), (key,value) ] list
        """
        result = []
        if not filename:
            filename = self.cfg_file
        for line in open(filename).readlines():
            ## Strip out new line characters
            line = line.strip()

            ## Skip blank lines
            if line == "":
                continue

            ## Skip comments
            if line[0] == "#" or line[0] == ';':
                continue
            tmp = line.split("=", 1)
            if len(tmp) < 2: continue
            key, value = tmp
            key = key.strip()
            value = value.strip()
            result.append( (key, value) )
        return result

    def _edit_static_file(self, attribute, new_value, filename=None, old_value=None, append=False):
        """ Modify a general config file (like nagios.cfg) that has a key=value config file format.

        Arguments:
            filename -- Name of config file that will be edited (i.e. nagios.cfg)
            attribute -- name of attribute to edit (i.e. check_external_commands)
            new_value -- new value for the said attribute (i.e. "1"). None deletes the line.
            old_value -- Useful if multiple attributes exist (i.e. cfg_dir) and you want to replace a specific one.
            append -- If true, do not overwrite current setting. Instead append this at the end. Use this with settings that are repeated like cfg_file.
        Examples:
            _edit_static_file(filename='/etc/nagios/nagios.cfg', attribute='check_external_commands', new_value='1')
            _edit_static_file(filename='/etc/nagios/nagios.cfg', attribute='cfg_dir', new_value='/etc/nagios/okconfig', append=True)
        """
        if filename is None:
            filename = self.cfg_file

        # For some specific attributes, append should be implied
        if attribute in ('cfg_file', 'cfg_dir', 'broker_module'):
            append = True

        # If/when we make a change, new_line is what will be written
        new_line = '%s=%s\n' % (attribute, new_value)

        # new_value=None means line should be removed
        if new_value is None:
            new_line = ''

        write_buffer = open(filename).readlines()
        is_dirty = False # dirty if we make any changes
        for i,line in enumerate(write_buffer):
            ## Strip out new line characters
            line = line.strip()

            ## Skip blank lines
            if line == "":
                continue

            ## Skip comments
            if line[0] == "#" or line[0] == ';':
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # If key does not match, we are not interested in this line
            if key != attribute:
                continue

            # If old_value was specified, and it matches, dont have to look any further
            elif value == old_value:
                write_buffer[i] = new_line
                is_dirty = True
                break
            # if current value is the same as new_value, no need to make changes
            elif value == new_value:
                return False
            # Special so cfg_dir matches despite double-slashes, etc
            elif attribute == 'cfg_dir' and os.path.normpath(value) == os.path.normpath(new_value):
                return False
            # We are not appending, and no old value was specified:
            elif append == False and not old_value:
                write_buffer[i] = new_line
                is_dirty = True
                break
        if is_dirty == False and new_value is not None:
            # If we get here, it means we read the whole file,
            # and we have not yet made any changes, So we assume
            # We should append to the file
            write_buffer.append(new_line)
            is_dirty = True
        # When we get down here, it is time to write changes to file
        if is_dirty == True:
            open(filename,'w').write(''.join(write_buffer))
            return True
        else:
            return False

    def needs_reload(self):
        """Returns True if Nagios service needs reload of cfg files

        Returns False if reload not needed or Nagios is not running
        """
        new_timestamps = self.get_timestamps()
        object_cache_file = self.get_cfg_value('object_cache_file')

        if self._get_pid() is None:
            return False
        if not object_cache_file:
            return True
        if not os.path.isfile(object_cache_file):
            return True
        object_cache_timestamp = new_timestamps.get(object_cache_file, 0)
        # Reload not needed if no object_cache file
        if object_cache_file is None:
            return False
        for k,v in new_timestamps.items():
            if not v or int(v) > object_cache_timestamp:
                return True
        return False
    def needs_reparse(self):
        """Returns True if any Nagios configuration file has changed since last parse()"""
        # If Parse has never been run:
        if self.data == {}:
            return True
        new_timestamps = self.get_timestamps()
        if len(new_timestamps) != len( self.timestamps ):
            return True
        for k,v in new_timestamps.items():
            if self.timestamps.get(k, None) != v:
                return True
        return False

    def parse_maincfg(self):
        """ Parses your main configuration (nagios.cfg) and stores it as key/value pairs in self.maincfg_values

        This function is mainly used by config.parse() which also parses your whole configuration set.
        """
        self.maincfg_values = self._load_static_file(self.cfg_file)
    def parse(self):
        """ Parse all objects in your nagios configuration

        This functions starts by loading up your nagios.cfg ( parse_maincfg() ) then moving on to
        your object configuration files (as defined via cfg_file and cfg_dir) and and your resource_file
        as well

        Returns:
          None

        Raises:
          IOError if unable to read any file due to permission problems
        """

        # reset
        self.reset()

        self.parse_maincfg()
        
        self.cfg_files = self.get_cfg_files()

        # When parsing config, we will softly fail if permission denied
        # comes on resource files. If later someone tries to get them via
        # get_resource, we will fail hard
        try:
            self._resource_values = self.get_resources()
        except IOError, e:
            self.errors.append( str(e) )
        
        self.timestamps = self.get_timestamps()
        
        ## This loads everything into
        for cfg_file in self.cfg_files:
            self._load_file(cfg_file)

        self._post_parse()

    def get_resource(self, resource_name):
        """ Get a single resource value which can be located in any resource.cfg file

         Arguments:
            resource_name: Name as it appears in resource file (i.e. $USER1$)
        Returns:
            String value of the resource value.
        Raises:
            * KeyError if resource is not found
            * ParserError if resource is not found and you do not have permissions
        """
        resources = self.get_resources()
        for k,v in resources:
            if k == resource_name:
                return v


    def get_timestamps(self):
        """Returns a hash map of all nagios related files and their timestamps"""
        files = {}
        files[self.cfg_file] = None
        for k,v in self.maincfg_values:
            if k in ('resource_file','lock_file','object_cache_file'):
                files[v] = None
        for i in self.get_cfg_files():
            files[i] = None
        # Now lets lets get timestamp of every file
        for k,v in files.items():
            if not os.path.isfile(k): continue
            files[k] = os.stat(k).st_mtime
        return files

    def get_resources(self):
        """Returns a list of every private resources from nagios.cfg"""
        resources = []
        for config_object,config_value in self.maincfg_values:
            if config_object == 'resource_file' and os.path.isfile(config_value):
                resources += self._load_static_file(config_value)
        return resources

    def extended_parse(self):
        """
        This parse is used after the initial parse() command is run.  It is
        only needed if you want extended meta information about hosts or other objects
        """
        ## Do the initial parsing
        self.parse()

        ## First, cycle through the hosts, and append hostgroup information
        index = 0
        for host in self.data['all_host']:
            if host.has_key('register') and host['register'] == '0': continue
            if not host.has_key('host_name'): continue
            if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
                self.data['all_host'][index]['meta']['hostgroup_list'] = []

            ## Append any hostgroups that are directly listed in the host definition
            if host.has_key('hostgroups'):
                for hostgroup_name in self._get_list(host, 'hostgroups'):
                    if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
                        self.data['all_host'][index]['meta']['hostgroup_list'] = []
                    if hostgroup_name not in self.data['all_host'][index]['meta']['hostgroup_list']:
                        self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup_name)

            ## Append any services which reference this host
            service_list = []
            for service in self.data['all_service']:
                if service.has_key('register') and service['register'] == '0': continue
                if not service.has_key('service_description'): continue
                if host['host_name'] in self._get_active_hosts(service):
                    service_list.append(service['service_description'])
            self.data['all_host'][index]['meta']['service_list'] = service_list

            ## Increment count
            index += 1

        ## Loop through all hostgroups, appending them to their respective hosts
        for hostgroup in self.data['all_hostgroup']:
            for member in self._get_list(hostgroup,'members'):
                index = 0
                for host in self.data['all_host']:
                    if not host.has_key('host_name'): continue

                    ## Skip members that do not match
                    if host['host_name'] == member:

                        ## Create the meta var if it doesn' exist
                        if not self.data['all_host'][index]['meta'].has_key('hostgroup_list'):
                            self.data['all_host'][index]['meta']['hostgroup_list'] = []

                        if hostgroup['hostgroup_name'] not in self.data['all_host'][index]['meta']['hostgroup_list']:
                            self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup['hostgroup_name'])

                    ## Increment count
                    index += 1

        ## Expand service membership
        index = 0
        for service in self.data['all_service']:

            ## Find a list of hosts to negate from the final list
            self.data['all_service'][index]['meta']['service_members'] = self._get_active_hosts(service)

            ## Increment count
            index += 1

    def _get_active_hosts(self, object):
        """
        Given an object, return a list of active hosts.  This will exclude hosts that ar negated with a "!"
        """
        ## First, generate the negation list
        negate_hosts = []

        ## Hostgroups
        if object.has_key("hostgroup_name"):

            for hostgroup_name in self._get_list(object, 'hostgroup_name'):
                if hostgroup_name[0] == "!":
                    hostgroup_obj = self.get_hostgroup(hostgroup_name[1:])
                    negate_hosts.extend(self._get_list(hostgroup_obj,'members'))

        ## Host Names
        if object.has_key("host_name"):
            for host_name in self._get_list(object, 'host_name'):
                if host_name[0] == "!":
                    negate_hosts.append(host_name[1:])

        ## Now get hosts that are actually listed
        active_hosts = []

        ## Hostgroups
        if object.has_key("hostgroup_name"):

            for hostgroup_name in self._get_list(object, 'hostgroup_name'):
                if hostgroup_name[0] != "!":
                    active_hosts.extend(self._get_list(self.get_hostgroup(hostgroup_name),'members'))

        ## Host Names
        if object.has_key("host_name"):
            for host_name in self._get_list(object, 'host_name'):
                if host_name[0] != "!":
                    active_hosts.append(host_name)

        ## Combine the lists
        return_hosts = []
        for active_host in active_hosts:
            if active_host not in negate_hosts:
                return_hosts.append(active_host)

        return return_hosts

    def get_cfg_dirs(self):
        """
        Return a list of all cfg directories used in this configuration

        Example:
        print get_cfg_dirs()
        ['/etc/nagios/hosts','/etc/nagios/objects',...]
        """
        cfg_dirs = []
        for config_object, config_value in self.maincfg_values:
            if config_object == "cfg_dir":
                cfg_dirs.append(config_value)
        return cfg_dirs

    def get_cfg_files(self):
        """
        Return a list of all cfg files used in this configuration

        Example:
        print get_cfg_files()
        ['/etc/nagios/hosts/host1.cfg','/etc/nagios/hosts/host2.cfg',...]
        """
        cfg_files = []
        for config_object, config_value in self.maincfg_values:
            
            ## Add cfg_file objects to cfg file list
            if config_object == "cfg_file" and os.path.isfile(config_value):
                cfg_files.append(config_value)

            ## Parse all files in a cfg directory
            if config_object == "cfg_dir":
                directories = []
                raw_file_list = []
                directories.append( config_value )
                # Walk through every subdirectory and add to our list
                while len(directories) > 0:
                    current_directory = directories.pop(0)
                    # Nagios doesnt care if cfg_dir exists or not, so why should we ?
                    if not os.path.isdir( current_directory ): continue
                    list = os.listdir(current_directory)
                    for item in list:
                        # Append full path to file
                        item = "%s" % (os.path.join(current_directory, item.strip()))
                        if os.path.islink( item ):
                            item = os.readlink( item )
                        if os.path.isdir(item):
                            directories.append( item )
                        if raw_file_list.count( item ) < 1:
                            raw_file_list.append( item )
                for raw_file in raw_file_list:
                    if raw_file.endswith('.cfg'):
                        if os.path.exists(raw_file) and not os.path.isdir(raw_file):
                            # Nagios doesnt care if cfg_file exists or not, so we will not throws errors
                            cfg_files.append(raw_file)

        return cfg_files
    def get_cfg_value(self, key):
        """ Returns one specific value from your nagios.cfg file, None if value is not found.
          Arguments:
            key - what attribute to fetch from nagios.cfg (example: "command_file" )
          Returns:
            String of the first value found for
          Example:
            >>> c = config()
            >>> log_file = c.get_cfg_value('log_file')

            # Should return something like "/var/log/nagios/nagios.log"
        """
        if self.maincfg_values == []:
            self.maincfg_values = self._load_static_file(self.cfg_file)
        for k,v in self.maincfg_values:
            if k == key:
                return v
        return None

    def get_object_types(self):
        """ Returns a list of all discovered object types """
        return map(lambda x: re.sub("all_", "", x), self.data.keys())

    def cleanup(self):
        """
        This cleans up dead configuration files
        """
        for filename in self.cfg_files:
            if os.path.isfile(filename):
                size = os.stat(filename)[6]
                if size == 0:
                    os.remove(filename)

        return True

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data[key]


class mk_livestatus:
    """ Wrapper around MK-Livestatus

    Example usage:
    s = mk_livestatus()
    for hostgroup s.get_hostgroups():
        print hostgroup['name'], hostgroup['num_hosts']
    """
    def __init__(self, livestatus_socket_path=None, nagios_cfg_file=None, authuser=None):
        """ Initilize a new instance of mk_livestatus

        Arguments:
          livestatus_socket_path -- Path to livestatus socket (if none specified, use one specified in nagios.cfg)
          nagios_cfg_file -- Path to your nagios.cfg. If None then try to auto-detect
          authuser -- If specified. Every data pulled is with the access rights of that contact.
        """
        if livestatus_socket_path is None:
            c = config(cfg_file=nagios_cfg_file)
            c.parse_maincfg()
            for k,v in c.maincfg_values:
                if k == 'broker_module' and v.find("livestatus.o") > -1:
                    tmp = v.split()
                    if len(tmp) > 1:
                        livestatus_socket_path = tmp[1]
        # If we get here then livestatus_socket_path should be resolved for us
        if livestatus_socket_path is None:
            raise ParserError("Could not find path to livestatus socket file. Please specify one or make sure livestatus broker_module is loaded")
        self.livestatus_socket_path = livestatus_socket_path
        self.authuser = authuser

    def test(self):
        """ Raises ParserError if there are problems communicating with livestatus socket """
        if not os.path.exists(self.livestatus_socket_path):
            raise ParserError("Livestatus socket file not found or permission denied (%s)" % self.livestatus_socket_path)
        try:
            self.query("GET hosts")
        except KeyError, e:
            raise ParserError("got '%s' when testing livestatus socket. error was: '%s'" % (type(e), e))
        return True
    def query(self, query, *args, **kwargs):

        columns = None # Here we will keep a list of column names
        doing_stats = False
        # We break query up into a list, of commands, then put it back into a line seperated
        # string before be talk to the socket
        query = query.split('\n')
        for i in args:
            query.append(i)
        if query[0].startswith('GET'):
            query.append("ResponseHeader: fixed16")
            query.append("OutputFormat: python")
            query.append("ColumnHeaders: on")
        for i in query:
            if i.startswith('Columns:'):
                columns = i[len('Columns:'):].split()
            if i.startswith('Stats'):
                doing_stats = True
        if not self.authuser is None and not self.authuser == '':
            query.append("AuthUser: %s" % self.authuser)
        query = '\n'.join(query) + '\n'
        self.last_query = query

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(self.livestatus_socket_path)
        except IOError:
            raise ParserError(
                "Could not connect to socket '%s'. Make sure nagios is running and mk_livestatus loaded."
                % self.livestatus_socket_path
            )
        try:
            s.send(query)
        except IOError:
            raise ParserError(
                "Could not write to socket '%s'. Make sure you the right permissions"
                % self.livestatus_socket_path
            )
        s.shutdown(socket.SHUT_WR)
        tmp = s.makefile()
        response_header = tmp.readline()
        if len(response_header) == 0:
            return []
        return_code = response_header.split()[0]
        answer = tmp.read()
        if not return_code.startswith('2'):
            raise ParserError("Error '%s' from livestatus socket\n%s" % (return_code,answer))
        if answer == '':
            return []

        # Turn livestatus response into a python object
        try:
            answer = eval(answer)
        except Exception, e:
            raise ParserError("Error, could not parse response from livestatus.\n%s" % (answer))

        s.close()
        # Workaround for livestatus bug, where column headers are not provided even if we asked for them
        if doing_stats == True and len(answer) == 1:
            return answer[0]

        columns = answer.pop(0)

        # If magic words "columns=False" is provided, we return an array of arrays instead of array of dicts
        if kwargs.get('columns') == False and len(answer) == 1:
            return answer.pop(0)

        # Lets throw everything into a hashmap before we return
        result = []
        for line in answer:
            tmp = {}
            for i,column in enumerate(line):
                column_name = columns[i]
                tmp[column_name] = column
            result.append(tmp)
        return result
    def get_host(self, host_name):
        return self.query('GET hosts', 'Filter: host_name = %s' % host_name)[0]
    def get_service(self, host_name, service_description):
        return self.query('GET services', 'Filter: host_name = %s' % host_name, 'Filter: description = %s' % service_description)[0]
    def get_hosts(self, *args):
        return self.query('GET hosts', *args)
    def get_services(self, *args):
        return self.query('GET services', *args)
    def get_hostgroups(self, *args):
        return self.query('GET hostgroups', *args)
    def get_contacts(self, *args):
        return self.query('GET contacts', *args)
    def get_contact(self, contact_name):
        return self.query('GET contacts', 'Filter: contact_name = %s' % contact_name)[0]


class retention:
    """ Easy way to parse the content of retention.dat

    After calling parse() contents of retention.dat are kept in self.data

    Example Usage:
    >>> #r = retention()
    >>> #r.parse()
    >>> #print r
    >>> #print r.data['info']
    """
    def __init__(self, filename=None, cfg_file=None ):
        """ Initilize a new instance of retention.dat

        Arguments (you only need to provide one of these):
            filename -- path to your retention.dat file
            cfg_file -- path to your nagios.cfg file, path to retention.dat
              will be looked up in this file
        """
        # If filename is not provided, lets try to discover it from
        # nagios.cfg
        if filename is None:
            c = config(cfg_file=cfg_file)
            for key,value in c._load_static_file():
                if key == "state_retention_file":
                    filename = value

        self.filename = filename
        self.data = None
    def parse(self):
        """ Parses your status.dat file and stores in a dictionary under self.data

        Returns:
            None
        Raises:
            ParserError -- if problem arises while reading status.dat
            ParserError -- if status.dat is not found
            IOError -- if status.dat cannot be read
        """
        self.data = {}
        status = {} # Holds all attributes of a single item
        key = None # if within definition, store everything before =
        value = None # if within definition, store everything after =
        lines = open(self.filename, 'rb').readlines()
        for sequence_no,line in enumerate( lines ):
            line_num = sequence_no + 1
            ## Cleanup and line skips
            line = line.strip()
            if line == "":
                pass
            elif line[0] == "#" or line[0] == ';':
                pass
            elif line.find("{") != -1:
                status = {}
                status['meta'] = {}
                status['meta']['type'] = line.split("{")[0].strip()
            elif line.find("}") != -1:
                # Status definition has finished, lets add it to
                # self.data
                if status['meta']['type'] not in self.data:
                    self.data[status['meta']['type']] = []
                self.data[status['meta']['type']].append(status)
            else:
                tmp = line.split("=", 1)
                if len(tmp) == 2:
                    (key, value) = line.split("=", 1)
                    status[key] = value
                elif key == "long_plugin_output":
                    # special hack for long_output support. We get here if:
                    # * line does not contain {
                    # * line does not contain }
                    # * line does not contain =
                    # * last line parsed started with long_plugin_output=
                    status[key] += "\n" + line
                else:
                    raise ParserError("Error on %s:%s: Could not parse line: %s" % (self.filename,line_num,line))
    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data[key]
    def __str__(self):
        if not self.data:
            self.parse()
        buffer = "# Generated by pynag"
        for datatype,datalist in self.data.items():
            for item in datalist:
                buffer += "%s {\n" % datatype
                for attr,value in item.items():
                    buffer += "%s=%s\n" % (attr,value)
                buffer += "}\n"
        return buffer
class status(retention):
    """ Easy way to parse status.dat file from nagios

    After calling parse() contents of status.dat are kept in status.data
    Example usage:
    >>> s = status(filename="status.dat")
    >>> s.parse()
    >>> keys = s.data.keys()
    >>> 'info' in keys
    True
    >>> 'programstatus' in keys
    True
    >>> for service in s.data.get('servicestatus',[]):
    ...     host_name=service.get('host_name', None)
    ...     description=service.get('service_description',None)
    """

    def __init__(self, filename=None, cfg_file=None ):
        """ Initilize a new instance of status

        Arguments (you only need to provide one of these):
            filename -- path to your status.dat file
            cfg_file -- path to your nagios.cfg file, path to status.dat
              will be looked up in this file
        """
        # If filename is not provided, lets try to discover it from
        # nagios.cfg
        if filename is None:
            c = config(cfg_file=cfg_file)
            for key,value in c._load_static_file():
                if key == "status_file":
                    filename = value

        self.filename = filename
        self.data = None

    def get_contactstatus(self, contact_name):
        """ Returns a dictionary derived from status.dat for one particular contact

        Returns:
            dict
        Raises:
            ValueError if object is not found
        >>> s = status(filename="status.dat")
        >>> s.get_contactstatus(contact_name='invalid_contact')
        ValueError('invalid_contact',)
        >>> first_contact = s.data['contactstatus'][0]['contact_name']
        >>> s.get_contactstatus(first_contact)['contact_name'] == first_contact
        True
        """
        if self.data is None:
            self.parse()
        for i in self.data['contactstatus']:
            if i.get('contact_name') == contact_name:
                return i
        return ValueError(contact_name)
    def get_hoststatus(self, host_name):
        """ Returns a dictionary derived from status.dat for one particular contact

        Returns:
            dict
        Raises:
            ValueError if object is not found
        """
        if self.data is None:
            self.parse()
        for i in self.data['hoststatus']:
            if i.get('host_name') == host_name:
                return i
        raise ValueError(host_name)
    def get_servicestatus(self, host_name, service_description):
        """ Returns a dictionary derived from status.dat for one particular service
        Returns:
            dict
        Raises:
            ValueError if object is not found
        """
        if self.data is None:
            self.parse()
        for i in self.data['servicestatus']:
            if i.get('host_name') == host_name:
                if i.get('service_description') == service_description:
                    return i
        raise ValueError(host_name, service_description)




class object_cache(config):
    """ Loads the configuration as it appears in objects.cache file """
    def get_cfg_files(self):
        for k,v in self.maincfg_values:
            if k == 'object_cache_file': return [ v ]



class ParserError(Exception):
    """ ParserError is used for errors that the Parser has when parsing config.

    Typical usecase when there is a critical error while trying to read configuration.
    """
    def __init__(self, message, item=None):
        self.message = message
        if item is None: return
        self.item = item
        self.filename = item['meta']['filename']

    def __str__(self):
        return repr(self.message)



class LogFiles(object):
    """ Parses Logfiles defined in nagios.cfg and allows easy access to its content in
        python-friendly arrays of dicts. Output should be more or less compatible with
        mk_livestatus log output
    """
    def __init__(self, maincfg=None):
        self.config = config(maincfg)
        self.log_file = self.config.get_cfg_value('log_file')
        self.log_archive_path = self.config.get_cfg_value('log_archive_path')
    def get_log_entries(self,start_time=None,end_time=None,strict=True,search=None,**kwargs):
        """ Get Parsed log entries for given timeperiod.
         Arguments:
            start_time -- unix timestamp. if None, return all entries from today
            end_time -- If specified, only fetch log entries older than this (unix timestamp)
            strict   -- If True, only return entries between start_time and end_time, if False,
                     -- then return entries that belong to same log files as given timeset
            search   -- If provided, only return log entries that contain this string (case insensitive)
            kwargs   -- All extra arguments are provided as filter on the log entries. f.e. host_name="localhost"
         Returns:
            List of dicts
        """
        now = time.time()
        if end_time is None:
            end_time = now
        if start_time is None:
            if 'filename' in kwargs:
                start_time = 1
            else:
                seconds_in_a_day = 60*60*24
                seconds_today = end_time % seconds_in_a_day # midnight of today
                start_time = end_time - seconds_today
        start_time = int(start_time)
        end_time = int(end_time)

        # Create an array of all logfiles, newest logfiles go to front of array
        logfiles = []
        for filename in os.listdir(self.log_archive_path):
            full_path = "%s/%s" % (self.log_archive_path, filename)
            logfiles.append(full_path)
        logfiles.append(self.log_file)
        logfiles.reverse()

        result = []
        if 'filename' in kwargs:
            logfiles = filter(lambda x: x == kwargs.get('filename'), logfiles)
        for log_file in logfiles:
            entries = self._parse_log_file(filename=log_file)
            if len(entries) == 0:
                continue
            first_entry = entries[0]
            last_entry = entries[len(entries)-1]

            if first_entry['time'] > end_time:
                continue
            # If strict, filter entries to only include the ones in the timespan
            if strict == True:
                entries = [x for x in entries if x['time'] >= start_time and x['time'] <= end_time]
            # If search string provided, filter the string
            if search is not None:
                entries = [x for x in entries if x['message'].lower().find(search.lower()) > -1]
            for k,v in kwargs.items():
                entries = [x for x in entries if x.get(k) == v]
            result += entries

            if start_time is None or int(start_time) >= int(first_entry.get('time')):
                break
        return result
    def get_flap_alerts(self, **kwargs):
        """ Same as self.get_log_entries, except return timeperiod transitions. Takes same parameters.
        """
        return self.get_log_entries(class_name="timeperiod transition",**kwargs)
    def get_notifications(self, **kwargs):
        """ Same as self.get_log_entries, except return only notifications. Takes same parameters.
        """
        return self.get_log_entries(class_name="notification",**kwargs)

    def get_state_history(self,start_time=None,end_time=None,host_name=None,service_description=None):
        """ Returns a list of dicts, with the state history of hosts and services. Parameters behaves similar to get_log_entries """

        log_entries = self.get_log_entries(start_time=start_time, end_time=end_time, strict=False, class_name='alerts')
        result = []
        last_state = {} #
        now = time.time()

        for line in log_entries:
            if 'state' not in line:
                continue
            line['duration'] = now - int(line.get('time'))
            if host_name is not None and host_name != line.get('host_name'):
                continue
            if service_description is not None and service_description != line.get('service_description'):
                continue
            if start_time is None:
                start_time = int(line.get('time'))

            short_name = "%s/%s" % (line['host_name'],line['service_description'])
            if short_name in last_state:
                last = last_state[short_name]
                last['end_time'] = line['time']
                last['duration'] = last['end_time'] - last['time']
                line['previous_state'] = last['state']
            last_state[short_name] = line


            if start_time is not None and int(start_time) > int(line.get('time')):
                continue
            if end_time is not None and int(end_time) < int(line.get('time')):
                continue

            result.append(line)
        return result
    def _parse_log_file(self,filename=None):
        """ Parses one particular nagios logfile into arrays of dicts.

            if filename is None, then log_file from nagios.cfg is used.
        """
        if filename is None:
            filename = self.log_file
        result = []
        for line in open(filename).readlines():
            parsed_entry = self._parse_log_line( line )
            if parsed_entry !=  {}:
                parsed_entry['filename'] = filename
                result.append(parsed_entry)
        return result
    def _parse_log_line(self, line):
        """ Parse one particular line in nagios logfile and return a dict. """
        m = re.search('^\[(.*?)\] (.*?): (.*)', line)
        if m is None:
            return {}
        line = line.strip()
        timestamp, logtype, options = m.groups()

        result = {}
        try:
            timestamp = int(timestamp)
        except ValueError:
            timestamp = 0
        result['time'] = int(timestamp)
        result['type'] = logtype
        result['options'] = options
        result['message'] = line
        result['class'] = 0 # unknown
        result['class_name'] = 'unclassified'
        if logtype in ('CURRENT HOST STATE', 'CURRENT SERVICE STATE', 'SERVICE ALERT', 'HOST ALERT'):
            result['class'] = 1
            result['class_name'] = 'alerts'
            if logtype.find('HOST') > -1:
                # This matches host current state:
                m = re.search('(.*?);(.*?);(.*);(.*?);(.*)', options)
                if m is None:
                    return result
                host, state, hard, check_attempt, plugin_output = m.groups()
                service_description=None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host,service_description,state,hard,check_attempt,plugin_output = m.groups()
            result['host_name'] = host
            result['service_description'] = service_description
            result['state'] = int( pynag.Plugins.state[state] )
            result['check_attempt'] = check_attempt
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif "NOTIFICATION" in logtype:
            result['class'] = 3
            result['class_name'] = 'notification'
            if logtype == 'SERVICE NOTIFICATION':
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                contact,host,service_description,state,command,plugin_output = m.groups()
            elif logtype == 'HOST NOTIFICATION':
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                contact,host,state,command,plugin_output = m.groups()
                service_description = None
            result['contact_name'] = contact
            result['host_name'] = host
            result['service_description'] = service_description
            try:
                result['state'] = int( pynag.Plugins.state[state] )
            except Exception:
                result['state'] = -1
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif logtype == "EXTERNAL COMMAND":
            result['class'] = 5
            result['class_name'] = 'command'
            m = re.search('(.*?);(.*)', options)
            if m is None:
                return result
            command_name,text = m.groups()
            result['command_name'] = command_name
            result['text'] = text
        elif logtype in ('PASSIVE SERVICE CHECK', 'PASSIVE HOST CHECK'):
            result['class'] = 4
            result['class_name'] = 'passive'
            if logtype.find('HOST') > -1:
                # This matches host current state:
                m = re.search('(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, state, plugin_output = m.groups()
                service_description=None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host,service_description,state,plugin_output = m.groups()
            result['host_name'] = host
            result['service_description'] = service_description
            result['state'] = state
            result['plugin_output'] = plugin_output
            result['text'] = plugin_output
        elif logtype in ('SERVICE FLAPPING ALERT', 'HOST FLAPPING ALERT'):
            result['class_name'] = 'flapping'
        elif logtype == 'TIMEPERIOD TRANSITION':
            result['class_name'] = 'timeperiod_transition'
        elif logtype == 'Warning':
            result['class_name'] = 'warning'
            result['state'] = "1"
            result['text'] = options
        if 'text' not in result:
            result['text'] = result['options']
        result['log_class'] = result['class'] # since class is a python keyword
        return result

if __name__ == '__main__':
    l = LogFiles()
    entries = l.get_log_entries(start_time=1358208000,end_time=1358243258,service_description=None,class_name='alerts')
    for i in entries:
            print i['message']
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint()
