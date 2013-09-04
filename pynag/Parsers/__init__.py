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
import sys
import socket  # for mk_livestatus

import pynag.Plugins
import pynag.Utils


def debug(text):
    debug = True
    if debug:
        print text


_sentinel = object()


class config:
    """
    Parse and write nagios config files
    """
    # Regex for beginning of object definition
    # We want everything that matches:
    # define <object_type> {
    __beginning_of_object = re.compile("^\s*define\s+(\w+)\s*\{?(.*)$")

    def __init__(self, cfg_file=None, strict=False):
        """

        Arguments:
          cfg_file -- Full path to nagios.cfg. If None, try to auto-discover location
          strict   -- if True, use stricter parsing which is more prone to raising exceptions
        """

        self.cfg_file = cfg_file  # Main configuration file
        self.strict = strict  # Use strict parsing or not

        # If nagios.cfg is not set, lets do some minor autodiscover.
        if self.cfg_file is None:
            self.cfg_file = self.guess_cfg_file()
        self.data = {}
        self.maincfg_values = []
        self._is_dirty = False

    def guess_nagios_directory(self):
        """ Returns a path to the nagios configuration directory on your system

        Use this function for determining the nagios config directory in your code
        """
        return os.path.dirname(self.guess_cfg_file())

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
        for file_path in possible_files:
            if os.path.isfile(file_path):
                return file_path
        raise ParserError('Could not find nagios.cfg')

    def reset(self):
        self.cfg_files = []  # List of other configuration files
        self.data = {}  # dict of every known object definition
        self.errors = []  # List of ParserErrors
        self.item_list = None
        self.item_cache = None
        self.maincfg_values = []  # The contents of main nagios.cfg
        self._resource_values = []  # The contents of any resource_files

        ## This is a pure listof all the key/values in the config files.  It
        ## shouldn't be useful until the items in it are parsed through with the proper
        ## 'use' relationships
        self.pre_object_list = []
        self.post_object_list = []
        self.object_type_keys = {
            'hostgroup': 'hostgroup_name',
            'hostextinfo': 'host_name',
            'host': 'host_name',
            'service': 'name',
            'servicegroup': 'servicegroup_name',
            'contact': 'contact_name',
            'contactgroup': 'contactgroup_name',
            'timeperiod': 'timeperiod_name',
            'command': 'command_name',
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

    def _get_key(self, object_type, user_key=None):
        """
        Return the correct 'key' for an item.  This is mainly a helper method
        for other methods in this class.  It is used to shorten code repitition
        """
        if not user_key and not object_type in self.object_type_keys:
            raise ParserError("Unknown key for object type:  %s\n" % object_type)

        ## Use a default key
        if not user_key:
            user_key = self.object_type_keys[object_type]

        return user_key

    def _get_item(self, item_name, item_type):
        """ Return an item from a list """
        # create local cache for performance optimizations. TODO: Rewrite functions that call this function
        if not self.item_list:
            self.item_list = self.pre_object_list
            self.item_cache = {}
            for item in self.item_list:
                if not "name" in item:
                    continue
                name = item['name']
                tmp_item_type = (item['meta']['object_type'])
                if not tmp_item_type in self.item_cache:
                    self.item_cache[tmp_item_type] = {}
                self.item_cache[tmp_item_type][name] = item
        my_cache = self.item_cache.get(item_type, None)
        if not my_cache:
            return None
        return my_cache.get(item_name, None)

    def _apply_template(self, original_item):
        """
        Apply all attributes of item named parent_name to "original_item".
        """
        # TODO: There is space for more performance tweaks here
        # If item does not inherit from anyone else, lets just return item as is.
        if 'use' not in original_item:
            return original_item
        object_type = original_item['meta']['object_type']
        # Performance tweak, if item has been parsed. Lets not do it again
        if original_item['meta']['raw_definition'] in self.item_apply_cache[object_type]:
            return self.item_apply_cache[object_type][original_item['meta']['raw_definition']]
            # End of performance tweak
        parent_names = original_item['use'].split(',')
        parent_items = []
        for parent_name in parent_names:
            parent_item = self._get_item(parent_name, object_type)
            if parent_item is None:
                error_string = "Can not find any %s named %s\n" % (object_type, parent_name)
                self.errors.append(ParserError(error_string, item=original_item))
                continue
                # Parent item probably has use flags on its own. So lets apply to parent first
            try:
                parent_item = self._apply_template(parent_item)
            except RuntimeError, e:
                self.errors.append(ParserError("Error while parsing item: %s (it might have circular use=)" % str(e),
                                               item=original_item))
            parent_items.append(parent_item)

        inherited_attributes = original_item['meta']['inherited_attributes']
        template_fields = original_item['meta']['template_fields']
        for parent_item in parent_items:
            for k, v in parent_item.iteritems():
                if k in ('use', 'register', 'meta', 'name'):
                    continue
                if k not in inherited_attributes:
                    inherited_attributes[k] = v
                if k not in original_item:
                    original_item[k] = v
                    template_fields.append(k)
        if 'name' in original_item:
            self.item_apply_cache[object_type][original_item['meta']['raw_definition']] = original_item
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

        meta = {
            'object_type': object_type,
            'filename': filename,
            'template_fields': [],
            'needs_commit': None,
            'delete_me': None,
            'defined_attributes': {},
            'inherited_attributes': {},
            'raw_definition': "define %s {\n\n}" % object_type,
        }
        return {'meta': meta}

    def _load_file(self, filename):
        """ Parsers filename with self.parse_filename and append results in self._pre_object_list

            This function is mostly here for backwards compatibility

            Arguments:
                filename -- the file to be parsed. This is supposed to a nagios object definition file

            Returns:
                None
        """
        for i in self.parse_file(filename):
            self.pre_object_list.append(i)

    def parse_file(self, filename):
        """ Parses a nagios object configuration file and returns lists of dictionaries.

         This is more or less a wrapper around config.parse_string, so reading documentation there
         is useful.
        """
        try:
            raw_string = open(filename, 'rb').read()
            return self.parse_string(raw_string, filename=filename)
        except IOError, e:
            parser_error = ParserError(e.strerror)
            parser_error.filename = e.filename
            self.errors.append(parser_error)
            return []

    def parse_string(self, string, filename='None'):
        """ Parses a string, and returns all object definitions in that string

        Arguments:
          string              -- A string containing one or more object definitions
          filename (optional) -- If filename is provided, it will be referenced when raising exceptions

        Examples:
          >>> test_string = "define host {\\nhost_name examplehost\\n}\\n"
          >>> test_string += "define service {\\nhost_name examplehost\\nservice_description example service\\n}\\n"
          >>> c = config()
          >>> result = c.parse_string(test_string)
          >>> for i in result: print i.get('host_name'), i.get('service_description', None)
          examplehost None
          examplehost example service

         Returns:
          A list of dictionaries, that look like self.data
        """
        append = ""
        current = None
        in_definition = {}
        tmp_buffer = []
        result = []

        for sequence_no, line in enumerate(string.splitlines(False)):
            line_num = sequence_no + 1

            # If previous line ended with backslash, treat this line as a
            # continuation of previous line
            if append:
                line = append + line
                append = None

            ## Cleanup and line skips
            line = line.strip()
            if line == "":
                continue
            if line[0] == "#" or line[0] == ';':
                continue

            # If this line ends with a backslash, continue directly to next line
            if line.endswith('\\'):
                append = line.strip('\\')
                continue

            if line.startswith('}'):  # end of object definition

                if not in_definition:
                    p = ParserError("Unexpected '}' found outside object definition in line %s" % line_num)
                    p.filename = filename
                    p.line_start = line_num
                    raise p

                in_definition = None
                current['meta']['line_end'] = line_num
                # Looks to me like nagios ignores everything after the } so why shouldn't we ?
                rest = line.split("}", 1)[1]

                tmp_buffer.append(line)
                try:
                    current['meta']['raw_definition'] = '\n'.join(tmp_buffer)
                except Exception:
                    raise ParserError("Encountered Unexpected end of object definition in file '%s'." % filename)
                result.append(current)

                ## Destroy the Nagios Object
                current = None
                continue

            elif line.startswith('define'):  # beginning of object definition
                if in_definition:
                    raise ParserError(
                        "Error: Unexpected start of object definition in file '%s' on line %d.  Make sure you close preceding objects before starting a new one." % (
                            filename, line_num))

                m = self.__beginning_of_object.search(line)

                tmp_buffer = [line]
                object_type = m.groups()[0]
                if self.strict and object_type not in self.object_type_keys.keys():
                    raise ParserError(
                        "Don't know any object definition of type '%s'. it is not in a list of known object definitions." % object_type)
                current = self.get_new_item(object_type, filename)
                current['meta']['line_start'] = line_num

                ## Start off an object
                in_definition = True

                # Looks to me like nagios ignores everything after the {, so why shouldn't we ?
                rest = m.groups()[1]
                continue
            else:  # In the middle of an object definition
                tmp_buffer.append('    ' + line)

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
                if (current['meta']['object_type'] == 'timeperiod') and key not in ('timeperiod_name', 'alias'):
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

        return result

    def _locate_item(self, item):
        """
        This is a helper function for anyone who wishes to modify objects. It takes "item", locates the
        file which is configured in, and locates exactly the lines which contain that definition.

        Returns tuple:
            (everything_before, object_definition, everything_after, filename)
            everything_before (list of lines) - Every line in filename before object was defined
            everything_after (list of lines) - Every line in "filename" after object was defined
            object_definition (list of lines) - Every line used to define our item in "filename"
            filename (string) - file in which the object was written to
        Raises:
            ValueError if object was not found in "filename"
        """
        if "filename" in item['meta']:
            filename = item['meta']['filename']
        else:
            raise ValueError("item does not have a filename")

        # Look for our item, store it as my_item
        for i in self.parse_file(filename):
            if self.compareObjects(item, i):
                my_item = i
                break
        else:
            raise ValueError("We could not find object in %s\n%s" % (filename, item))

        # Caller of this method expects to be returned
        # several lists that describe the lines in our file.
        # The splitting logic starts here.
        my_file = open(filename)
        all_lines = my_file.readlines()
        my_file.close()

        start = my_item['meta']['line_start'] - 1
        end = my_item['meta']['line_end']
        everything_before = all_lines[:start]
        object_definition = all_lines[start:end]
        everything_after = all_lines[end:]
        return everything_before, object_definition, everything_after, filename

    def _modify_object(self, item, field_name=None, new_value=None, new_field_name=None, new_item=None,
                       make_comments=False):
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
        if item is None:
            return
        if field_name is None and new_item is None:
            raise ValueError("either field_name or new_item must be set")
        everything_before, object_definition, everything_after, filename = self._locate_item(item)
        if new_item is not None:
            # We have instruction on how to write new object, so we dont need to parse it
            object_definition = [new_item]
        else:
            change = None
            value = None
            i = 0
            for i in range(len(object_definition)):
                tmp = object_definition[i].split(None, 1)
                if len(tmp) == 0:
                    continue
                # Hack for timeperiods, they dont work like other objects
                elif item['meta']['object_type'] == 'timeperiod' and field_name not in ('alias', 'timeperiod_name'):
                    tmp = [object_definition[i]]
                    # we can't change timeperiod, so we fake a field rename
                    if new_value is not None:
                        new_field_name = new_value
                        new_value = None
                        value = ''
                elif len(tmp) == 1:
                    value = ''
                else:
                    value = tmp[1]
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
                        change = "\t%s\n" % new_field_name
                    object_definition[i] = change
                    break
            if not change and new_value is not None:
                # Attribute was not found. Lets add it
                change = "\t%-30s%s\n" % (field_name, new_value)
                object_definition.insert(i, change)
            # Lets put a banner in front of our item
        if make_comments:
            comment = '# Edited by PyNag on %s\n' % time.ctime()
            if len(everything_before) > 0:
                last_line_before = everything_before[-1]
                if last_line_before.startswith('# Edited by PyNag on'):
                    everything_before.pop()  # remove this line
            object_definition.insert(0, comment)
            # Here we overwrite the config-file, hoping not to ruin anything
        str_buffer = "%s%s%s" % (''.join(everything_before), ''.join(object_definition), ''.join(everything_after))
        self.write(filename, str_buffer)
        return True

    @pynag.Utils.synchronized(pynag.Utils.rlock)
    def write(self, filename, string):
        """ Wrapper around open(filename).write() """
        fh = open(filename, 'w')
        return_code = fh.write(string)
        fh.flush()
        os.fsync(fh)
        fh.close()
        self._is_dirty = True
        return return_code

    def item_rewrite(self, item, str_new_item):
        """ Completely rewrites item with string provided.

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
        """ Delete one specific item from its configuration files

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
        """ Modifies one field of a (currently existing) object. Changes are immediate (i.e. there is no commit)

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
        """ Removes one field of a (currently existing) object. Changes are immediate (i.e. there is no commit)

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
        """ Renames a field of a (currently existing) item. Changes are immediate (i.e. there is no commit).

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
        """ Adds a new object to a specified config file

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

        str_buffer = self.print_conf(item)
        fh = open(filename, 'a')
        fh.write(str_buffer)
        fh.close()
        return True

    def edit_object(self, item, field_name, new_value):
        """ Modifies a (currently existing) item. Changes are immediate (i.e. there is no commit)

        Example Usage: edit_object( item, field_name="host_name", new_value="examplehost.example.com")

        THIS FUNCTION IS DEPRECATED. USE item_edit_field() instead
        """
        return self.item_edit_field(item=item, field_name=field_name, new_value=new_value)

    def compareObjects(self, item1, item2):
        """ Compares two items. Returns true if they are equal """
        keys1 = item1['meta']['defined_attributes'].keys()
        keys2 = item2['meta']['defined_attributes'].keys()
        keys1.sort()
        keys2.sort()
        result = True
        if keys1 != keys2:
            return False
        for key in keys1:
            if key == 'meta':
                continue
            key1 = item1[key]
            key2 = item2[key]
            # For our purpose, 30 is equal to 30.000
            if key == 'check_interval':
                key1 = int(float(key1))
                key2 = int(float(key2))
            if str(key1) != str(key2):
                result = False
        if result == False:
            return False
        return True

    def edit_service(self, target_host, service_description, field_name, new_value):
        """ Edit a service's attributes """

        original_object = self.get_service(target_host, service_description)
        if original_object is None:
            raise ParserError("Service not found")
        return self.edit_object(original_object, field_name, new_value)

    def _get_list(self, item, key):
        """ Return a comma list from an item

        Example:

        _get_list(Foo_object, host_name)
        define service {
            service_description Foo
            host_name            larry,curly,moe
        }

        return
        ['larry','curly','moe']
        """
        if type(item) != type({}):
            raise ParserError("%s is not a dictionary\n" % item)
            # return []
        if not key in item:
            return []

        return_list = []

        if item[key].find(",") != -1:
            for name in item[key].split(","):
                return_list.append(name)
        else:
            return_list.append(item[key])

        ## Alphabetize
        return_list.sort()

        return return_list

    def delete_object(self, object_type, object_name, user_key=None):
        """ Delete object from configuration files """
        item = self.get_object(object_type=object_type, object_name=object_name, user_key=user_key)
        return self.item_remove(item)

    def delete_service(self, service_description, host_name):
        """ Delete service from configuration files """
        item = self.get_service(host_name, service_description)
        return self.item_remove(item)

    def delete_host(self, object_name, user_key=None):
        """ Delete a host from its configuration files """
        return self.delete_object('host', object_name, user_key=user_key)

    def delete_hostgroup(self, object_name, user_key=None):
        """ Delete a hostgroup from its configuration files """
        return self.delete_object('hostgroup', object_name, user_key=user_key)

    def get_object(self, object_type, object_name, user_key=None):
        """ Return a complete object dictionary

            Returns None if object is not found
        """
        object_key = self._get_key(object_type, user_key)
        for item in self.data['all_%s' % object_type]:
            if item.get(object_key, None) == object_name:
                return item
        return None

    def get_host(self, object_name, user_key=None):
        """ Return a host object """
        return self.get_object('host', object_name, user_key=user_key)

    def get_servicegroup(self, object_name, user_key=None):
        """ Return a Servicegroup object """
        return self.get_object('servicegroup', object_name, user_key=user_key)

    def get_contact(self, object_name, user_key=None):
        """ Return a Contact object """
        return self.get_object('contact', object_name, user_key=user_key)

    def get_contactgroup(self, object_name, user_key=None):
        """ Return a Contactgroup object """
        return self.get_object('contactgroup', object_name, user_key=user_key)

    def get_timeperiod(self, object_name, user_key=None):
        """ Return a Timeperiod object """
        return self.get_object('timeperiod', object_name, user_key=user_key)

    def get_command(self, object_name, user_key=None):
        """ Return a Command object """
        return self.get_object('command', object_name, user_key=user_key)

    def get_hostgroup(self, object_name, user_key=None):
        """ Return a hostgroup object """
        return self.get_object('hostgroup', object_name, user_key=user_key)

    def get_servicedependency(self, object_name, user_key=None):
        """ Return a servicedependency object """
        return self.get_object('servicedependency', object_name, user_key=user_key)

    def get_hostdependency(self, object_name, user_key=None):
        """ Return a hostdependency object """
        return self.get_object('hostdependency', object_name, user_key=user_key)

    def get_service(self, target_host, service_description):
        """ Return a service object """
        for item in self.data['all_service']:
            if item.get('service_description') == service_description and item.get('host_name') == target_host:
                return item
        return None

    def _append_use(self, source_item, name):
        """ Append attributes to source_item that are inherited via 'use' attribute'

        Attributes:
          source_item  -- item (dict) to apply the inheritance upon
          name         -- obsolete (discovered automatically via source_item['use']. Here for compatibility.
        """
        ## Remove the 'use' key
        if "use" in source_item:
            del source_item['use']

        for possible_item in self.pre_object_list:
            if "name" in possible_item:
                ## Start appending to the item
                for k, v in possible_item.iteritems():

                    try:
                        if k == 'use':
                            source_item = self._append_use(source_item, v)
                    except Exception:
                        raise ParserError("Recursion error on %s %s" % (source_item, v))

                    ## Only add the item if it doesn't already exist
                    if not k in source_item:
                        source_item[k] = v
        return source_item

    def _post_parse(self):
        self.item_list = None
        self.item_apply_cache = {}  # This is performance tweak used by _apply_template
        for raw_item in self.pre_object_list:
            # Performance tweak, make sure hashmap exists for this object_type
            object_type = raw_item['meta']['object_type']
            if not object_type in self.item_apply_cache:
                self.item_apply_cache[object_type] = {}
                # Tweak ends
            if "use" in raw_item:
                raw_item = self._apply_template(raw_item)
            self.post_object_list.append(raw_item)
            ## Add the items to the class lists.
        for list_item in self.post_object_list:
            type_list_name = "all_%s" % list_item['meta']['object_type']
            if not type_list_name in self.data:
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
                    filename = item['meta']['filename']
                    self.write(filename, file_contents)

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
        if "hostgroup_list" in item['meta']:
            output += "# Hostgroups: %s\n" % ",".join(item['meta']['hostgroup_list'])

        ## Some hostgroup information
        if "service_list" in item['meta']:
            output += "# Services: %s\n" % ",".join(item['meta']['service_list'])

        ## Some hostgroup information
        if "service_members" in item['meta']:
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
                    output += "\t %-30s %-30s\n" % (k, v)

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
            if len(tmp) < 2:
                continue
            key, value = tmp
            key = key.strip()
            value = value.strip()
            result.append((key, value))
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
        is_dirty = False  # dirty if we make any changes
        for i, line in enumerate(write_buffer):
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
            elif attribute == 'cfg_dir' and new_value and os.path.normpath(value) == os.path.normpath(new_value):
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
            str_buffer = ''.join(write_buffer)
            self.write(filename, str_buffer)
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
        for k, v in new_timestamps.items():
            if not v or int(v) > object_cache_timestamp:
                return True
        return False

    def needs_reparse(self):
        """Returns True if any Nagios configuration file has changed since last parse()"""
        # If Parse has never been run:
        if self.data == {}:
            return True
        # If previous save operation has forced a reparse
        if self._is_dirty is True:
            return True

        # If we get here, we check the timestamps of the configs
        new_timestamps = self.get_timestamps()
        if len(new_timestamps) != len(self.timestamps):
            return True
        for k, v in new_timestamps.items():
            if self.timestamps.get(k, None) != v:
                return True
        return False

    @pynag.Utils.synchronized(pynag.Utils.rlock)
    def parse_maincfg(self):
        """ Parses your main configuration (nagios.cfg) and stores it as key/value pairs in self.maincfg_values

        This function is mainly used by config.parse() which also parses your whole configuration set.
        """
        self.maincfg_values = self._load_static_file(self.cfg_file)

    @pynag.Utils.synchronized(pynag.Utils.rlock)
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
            self.errors.append(str(e))

        self.timestamps = self.get_timestamps()

        ## This loads everything into
        for cfg_file in self.cfg_files:
            self._load_file(cfg_file)

        self._post_parse()

        self._is_dirty = False

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
        for k, v in resources:
            if k == resource_name:
                return v

    def get_timestamps(self):
        """Returns hash map of all nagios related files and their timestamps"""
        files = {}
        files[self.cfg_file] = None
        for k, v in self.maincfg_values:
            if k in ('resource_file', 'lock_file', 'object_cache_file'):
                files[v] = None
        for i in self.get_cfg_files():
            files[i] = None
            # Now lets lets get timestamp of every file
        for k, v in files.items():
            if not os.path.isfile(k):
                continue
            files[k] = os.stat(k).st_mtime
        return files

    def get_resources(self):
        """Returns a list of every private resources from nagios.cfg"""
        resources = []
        for config_object, config_value in self.maincfg_values:
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
            if host.get("register", None) == "0":
                continue
            if not "host_name" in host:
                continue
            if not "hostgroup_list" in self.data['all_host'][index]['meta']:
                self.data['all_host'][index]['meta']['hostgroup_list'] = []

            ## Append any hostgroups that are directly listed in the host definition
            if "hostgroups" in host:
                for hostgroup_name in self._get_list(host, 'hostgroups'):
                    if not "hostgroup_list" in self.data['all_host'][index]['meta']:
                        self.data['all_host'][index]['meta']['hostgroup_list'] = []
                    if hostgroup_name not in self.data['all_host'][index]['meta']['hostgroup_list']:
                        self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup_name)

            ## Append any services which reference this host
            service_list = []
            for service in self.data['all_service']:
                if service.get("register", None) == "0":
                    continue
                if not "service_description" in service:
                    continue
                if host['host_name'] in self._get_active_hosts(service):
                    service_list.append(service['service_description'])
            self.data['all_host'][index]['meta']['service_list'] = service_list

            ## Increment count
            index += 1

        ## Loop through all hostgroups, appending them to their respective hosts
        for hostgroup in self.data['all_hostgroup']:
            for member in self._get_list(hostgroup, 'members'):
                index = 0
                for host in self.data['all_host']:
                    if not "host_name" in host:
                        continue

                    ## Skip members that do not match
                    if host['host_name'] == member:

                        ## Create the meta var if it doesn' exist
                        if not "hostgroup_list" in self.data['all_host'][index]['meta']:
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

    def _get_active_hosts(self, item):
        """
        Given an object, return a list of active hosts.  This will exclude hosts that ar negated with a "!"
        """
        ## First, generate the negation list
        negate_hosts = []

        ## Hostgroups
        if "hostgroup_name" in item:
            for hostgroup_name in self._get_list(item, 'hostgroup_name'):
                if hostgroup_name[0] == "!":
                    hostgroup_obj = self.get_hostgroup(hostgroup_name[1:])
                    negate_hosts.extend(self._get_list(hostgroup_obj, 'members'))

        ## Host Names
        if "host_name" in item:
            for host_name in self._get_list(item, 'host_name'):
                if host_name[0] == "!":
                    negate_hosts.append(host_name[1:])

        ## Now get hosts that are actually listed
        active_hosts = []

        ## Hostgroups
        if "hostgroup_name" in item:
            for hostgroup_name in self._get_list(item, 'hostgroup_name'):
                if hostgroup_name[0] != "!":
                    active_hosts.extend(self._get_list(self.get_hostgroup(hostgroup_name), 'members'))

        ## Host Names
        if "host_name" in item:
            for host_name in self._get_list(item, 'host_name'):
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

        Filenames are normalised so that if nagios.cfg specifies relative filenames
        we will convert it to fully qualified filename before returning.

        Example:
        print get_cfg_files()
        ['/etc/nagios/hosts/host1.cfg','/etc/nagios/hosts/host2.cfg',...]
        """
        cfg_files = []
        for config_object, config_value in self.maincfg_values:

            ## Add cfg_file objects to cfg file list
            if config_object == "cfg_file":
                config_value = self.abspath(config_value)
                if os.path.isfile(config_value):
                    cfg_files.append(config_value)

            ## Parse all files in a cfg directory
            if config_object == "cfg_dir":
                config_value = self.abspath(config_value)
                directories = []
                raw_file_list = []
                directories.append(config_value)
                # Walk through every subdirectory and add to our list
                while directories:
                    current_directory = directories.pop(0)
                    # Nagios doesnt care if cfg_dir exists or not, so why should we ?
                    if not os.path.isdir(current_directory):
                        continue
                    for item in os.listdir(current_directory):
                        # Append full path to file
                        item = "%s" % (os.path.join(current_directory, item.strip()))
                        if os.path.islink(item):
                            item = os.readlink(item)
                        if os.path.isdir(item):
                            directories.append(item)
                        if raw_file_list.count(item) < 1:
                            raw_file_list.append(item)
                for raw_file in raw_file_list:
                    if raw_file.endswith('.cfg'):
                        if os.path.exists(raw_file) and not os.path.isdir(raw_file):
                            # Nagios doesnt care if cfg_file exists or not, so we will not throws errors
                            cfg_files.append(raw_file)

        return cfg_files

    def abspath(self, path):
        """ Return the absolute path of a given relative path.

         The current working directory is assumed to be the dirname of nagios.cfg

         Example:
         >>> c = config(cfg_file="/etc/nagios/nagios.cfg")
         >>> c.abspath('nagios.cfg')
         '/etc/nagios/nagios.cfg'
         >>> c.abspath('/etc/nagios/nagios.cfg')
         '/etc/nagios/nagios.cfg'
        """
        if not isinstance(path, str):
            return ValueError("Path must be a string got %s instead" % type(path))
        if path.startswith('/'):
            return path
        nagiosdir = os.path.dirname(self.cfg_file)
        normpath = os.path.abspath(os.path.join(nagiosdir, path))
        return normpath

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
        for k, v in self.maincfg_values:
            if k == key:
                return v
        return None

    def get_object_types(self):
        """ Returns a list of all discovered object types """
        return map(lambda x: re.sub("all_", "", x), self.data.keys())

    def cleanup(self):
        """ Remove configuration files that have no configuration items"""
        for filename in self.cfg_files:
            if not self.parse_file(filename):  # parse_file returns empty list on empty files
                os.remove(filename)
                # If nagios.cfg specifies this file directly via cfg_file directive then...
                for k, v in self.maincfg_values:
                    if k == 'cfg_file' and v == filename:
                        self._edit_static_file(k, old_value=v, new_value=None)

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
            for k, v in c.maincfg_values:
                if k == 'broker_module' and v.find("livestatus.o") > -1:
                    tmp = v.split()
                    if len(tmp) > 1:
                        livestatus_socket_path = tmp[1]
            # If we get here then livestatus_socket_path should be resolved for us
        if livestatus_socket_path is None:
            msg = "No Livestatus socket define. Make sure livestatus broker module is loaded."
            raise ParserError(msg)
        self.livestatus_socket_path = livestatus_socket_path
        self.authuser = authuser

    def test(self):
        """ Raises ParserError if there are problems communicating with livestatus socket """
        if not os.path.exists(self.livestatus_socket_path):
            raise ParserError(
                "Livestatus socket file not found or permission denied (%s)" % self.livestatus_socket_path)
        try:
            self.query("GET hosts")
        except KeyError, e:
            raise ParserError("got '%s' when testing livestatus socket. error was: '%s'" % (type(e), e))
        return True

    def _get_socket(self):
        """ Return a socket.socket() instance which we can use to communicate with livestatus

         Socket might be either unix filesocket or a tcp socket depenging in the content of
         self.livestatus_socket_path


        """
        try:
            # If livestatus_socket_path contains a colon, then we assume that it is tcp socket instead of a local filesocket
            if self.livestatus_socket_path.find(':') > 0:
                address, tcp_port = self.livestatus_socket_path.split(':', 1)
                if not tcp_port.isdigit():
                    msg = 'Could not parse host:port "%s". %s  does not look like a valid port is not a valid tcp port.'
                    raise ParserError(msg % (self.livestatus_socket_path, tcp_port))
                tcp_port = int(tcp_port)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((address, tcp_port))
            else:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(self.livestatus_socket_path)
            return s
        except IOError, e:
            msg = "%s while connecting to '%s'. Make sure nagios is running and mk_livestatus loaded."
            raise ParserError(msg % (e, self.livestatus_socket_path))

    def query(self, query, *args, **kwargs):

        # We break query up into a list, of commands, then before sending command to the socket
        # We will write it one line per item in the array
        query = query.split('\n')
        for i in args:
            query.append(i)

        # If no response header was specified, we add fixed16
        response_header = None
        if not filter(lambda x: x.startswith('ResponseHeader:'), query):
            query.append("ResponseHeader: fixed16")
            response_header = "fixed16"

        # If no specific outputformat is requested, we will return in python format
        python_format = False
        if not filter(lambda x: x.startswith('OutputFormat:'), query):
            query.append("OutputFormat: python")
            python_format = True

        # There is a bug in livestatus where if requesting Stats, then no column headers are sent from livestatus
        # In later version, the headers are sent, but the output is corrupted.
        #
        # We maintain consistency by clinging on to the old bug, and if there are Stats in the output
        # we will not ask for column headers
        doing_stats = len(filter(lambda x: x.startswith('Stats:'), query)) > 0
        if not filter(lambda x: x.startswith('Stats:'), query) and not filter(
                lambda x: x.startswith('ColumnHeaders: on'), query):
            query.append("ColumnHeaders: on")

        # Check if we need to add authuser to the query
        if not filter(lambda x: x.startswith('AuthUser:'), query) and self.authuser not in (None, ''):
            query.append("AuthUser: %s" % self.authuser)

        # When we reach here, we are done adding options to the query, so we convert to the string that will
        # be sent to the livestatus socket
        query = '\n'.join(query) + '\n'
        self.last_query = query

        #
        # Lets create a socket and see if we can write to it
        #
        s = self._get_socket()
        try:
            s.send(query)
        except IOError:
            msg = "Could not write to socket '%s'. Make sure you have the right permissions"
            raise ParserError(msg % self.livestatus_socket_path)
        s.shutdown(socket.SHUT_WR)
        tmp = s.makefile()

        # Read the response header from livestatus
        if response_header == "fixed16":
            response_data = tmp.readline()
            if len(response_data) == 0:
                return []
            return_code = response_data.split()[0]
            if not return_code.startswith('2'):
                error_message = tmp.readline().strip()
                raise ParserError("Error '%s' from livestatus: %s" % (return_code, error_message))

        answer = tmp.read()
        # We are done with the livestatus socket. lets close it
        s.close()

        if answer == '':
            return []

        # If something other than python format was requested, we return the answer as is
        if python_format == False:
            return answer

        # If we reach down here, it means we are supposed to parse the output before returning it
        try:
            answer = eval(answer)
        except Exception, e:
            raise ParserError("Error, could not parse response from livestatus.\n%s" % answer)

        # Workaround for livestatus bug, where column headers are not provided even if we asked for them
        if doing_stats == True and len(answer) == 1:
            return answer[0]

        columns = answer.pop(0)

        # Lets throw everything into a hashmap before we return
        result = []
        for line in answer:
            tmp = {}
            for i, column in enumerate(line):
                column_name = columns[i]
                tmp[column_name] = column
            result.append(tmp)
        return result

    def get_host(self, host_name):
        return self.query('GET hosts', 'Filter: host_name = %s' % host_name)[0]

    def get_service(self, host_name, service_description):
        return self.query('GET services', 'Filter: host_name = %s' % host_name,
                          'Filter: description = %s' % service_description)[0]

    def get_hosts(self, *args):
        return self.query('GET hosts', *args)

    def get_services(self, *args):
        return self.query('GET services', *args)

    def get_hostgroups(self, *args):
        return self.query('GET hostgroups', *args)

    def get_servicegroups(self, *args):
        return self.query('GET servicegroups', *args)

    def get_contactgroups(self, *args):
        return self.query('GET contactgroups', *args)

    def get_contacts(self, *args):
        return self.query('GET contacts', *args)

    def get_contact(self, contact_name):
        return self.query('GET contacts', 'Filter: contact_name = %s' % contact_name)[0]

    def get_servicegroup(self, name):
        return self.query('GET servicegroups', 'Filter: name = %s' % name)[0]

    def get_hostgroup(self, name):
        return self.query('GET hostgroups', 'Filter: name = %s' % name)[0]

    def get_contactgroup(self, name):
        return self.query('GET contactgroups', 'Filter: name = %s' % name)[0]


class retention:
    """ Easy way to parse the content of retention.dat

    After calling parse() contents of retention.dat are kept in self.data

    Example Usage:
    >>> #r = retention()
    >>> #r.parse()
    >>> #print r
    >>> #print r.data['info']
    """

    def __init__(self, filename=None, cfg_file=None):
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
            for key, value in c._load_static_file():
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
        status = {}  # Holds all attributes of a single item
        key = None  # if within definition, store everything before =
        value = None  # if within definition, store everything after =
        if not self.filename:
            raise ParserError("status.dat file not found")
        lines = open(self.filename, 'rb').readlines()
        for sequence_no, line in enumerate(lines):
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
                    raise ParserError("Error on %s:%s: Could not parse line: %s" % (self.filename, line_num, line))

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        if not self.data:
            self.parse()
        str_buffer = "# Generated by pynag"
        for datatype, datalist in self.data.items():
            for item in datalist:
                str_buffer += "%s {\n" % datatype
                for attr, value in item.items():
                    str_buffer += "%s=%s\n" % (attr, value)
                str_buffer += "}\n"
        return str_buffer


class status(retention):
    """ Easy way to parse status.dat file from nagios

    After calling parse() contents of status.dat are kept in status.data
    Example usage:
    >>> s = status()
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

    def __init__(self, filename=None, cfg_file=None):
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
            for key, value in c._load_static_file():
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
        >>> s = status()
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
        for k, v in self.maincfg_values:
            if k == 'object_cache_file':
                return [v]


class ParserError(Exception):
    """ ParserError is used for errors that the Parser has when parsing config.

    Typical usecase when there is a critical error while trying to read configuration.
    """
    filename = None
    line_start = None
    message = None

    def __init__(self, message, item=None):
        self.message = message
        if item is None:
            return
        self.item = item
        self.filename = item['meta']['filename']
        self.line_start = item['meta'].get('line_start')

    def __str__(self):
        message = self.message
        if self.filename and self.line_start:
            message = '%s in %s, line %s' % (message, self.filename, self.line_start)
        return repr(message)


class LogFiles(object):
    """ Parses Logfiles defined in nagios.cfg and allows easy access to its content in
        python-friendly arrays of dicts. Output should be more or less compatible with
        mk_livestatus log output
    """

    def __init__(self, maincfg=None):
        self.config = config(maincfg)
        self.log_file = self.config.get_cfg_value('log_file')
        self.log_archive_path = self.config.get_cfg_value('log_archive_path')

    def get_log_entries(self, start_time=None, end_time=None, strict=True, search=None, **kwargs):
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
                seconds_in_a_day = 60 * 60 * 24
                seconds_today = end_time % seconds_in_a_day  # midnight of today
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
            last_entry = entries[len(entries) - 1]

            if first_entry['time'] > end_time:
                continue
                # If strict, filter entries to only include the ones in the timespan
            if strict == True:
                entries = [x for x in entries if x['time'] >= start_time and x['time'] <= end_time]
                # If search string provided, filter the string
            if search is not None:
                entries = [x for x in entries if x['message'].lower().find(search.lower()) > -1]
            for k, v in kwargs.items():
                entries = [x for x in entries if x.get(k) == v]
            result += entries

            if start_time is None or int(start_time) >= int(first_entry.get('time')):
                break
        return result

    def get_flap_alerts(self, **kwargs):
        """ Same as self.get_log_entries, except return timeperiod transitions. Takes same parameters.
        """
        return self.get_log_entries(class_name="timeperiod transition", **kwargs)

    def get_notifications(self, **kwargs):
        """ Same as self.get_log_entries, except return only notifications. Takes same parameters.
        """
        return self.get_log_entries(class_name="notification", **kwargs)

    def get_state_history(self, start_time=None, end_time=None, host_name=None, service_description=None):
        """ Returns a list of dicts, with the state history of hosts and services. Parameters behaves similar to get_log_entries """

        log_entries = self.get_log_entries(start_time=start_time, end_time=end_time, strict=False, class_name='alerts')
        result = []
        last_state = {}
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

            short_name = "%s/%s" % (line['host_name'], line['service_description'])
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

    def _parse_log_file(self, filename=None):
        """ Parses one particular nagios logfile into arrays of dicts.

            if filename is None, then log_file from nagios.cfg is used.
        """
        if filename is None:
            filename = self.log_file
        result = []
        for line in open(filename).readlines():
            parsed_entry = self._parse_log_line(line)
            if parsed_entry != {}:
                parsed_entry['filename'] = filename
                result.append(parsed_entry)
        return result

    def _parse_log_line(self, line):
        """ Parse one particular line in nagios logfile and return a dict. """
        host = None
        service_description = None
        state = None
        check_attempt = None
        plugin_output = None
        contact = None

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
        result['class'] = 0  # unknown
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
                service_description = None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, service_description, state, hard, check_attempt, plugin_output = m.groups()
            result['host_name'] = host
            result['service_description'] = service_description
            result['state'] = int(pynag.Plugins.state[state])
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
                contact, host, service_description, state, command, plugin_output = m.groups()
            elif logtype == 'HOST NOTIFICATION':
                m = re.search('(.*?);(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                contact, host, state, command, plugin_output = m.groups()
                service_description = None
            result['contact_name'] = contact
            result['host_name'] = host
            result['service_description'] = service_description
            try:
                result['state'] = int(pynag.Plugins.state[state])
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
            command_name, text = m.groups()
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
                service_description = None
            if logtype.find('SERVICE') > -1:
                m = re.search('(.*?);(.*?);(.*?);(.*)', options)
                if m is None:
                    return result
                host, service_description, state, plugin_output = m.groups()
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
        result['log_class'] = result['class']  # since class is a python keyword
        return result


class ExtraOptsParser(object):
    """ Get Nagios Extra-Opts from a config file as specified by http://nagiosplugins.org/extra-opts

        We could ALMOST use pythons ConfParser but nagios plugin team thought it would be a
        good idea to support multiple values per key, so a dict datatype no longer works.

        Its a shame because we have to make our own "ini" parser as a result

        Usage:

        # cat /etc/nagios/plugins.ini
        [main]
        host_name = localhost
        [other section]
        host_name = example.com
        # EOF

        e = ExtraOptsParser(section_name='main', config_file='/etc/nagios/plugins.ini')
        e.get('host_name')  # returns "localhost"
        e.get_values()  # Returns a dict of all the extra opts
        e.getlist('host_name')  # returns all values of host_name (if more than one were specified) in a list



    """
    standard_locations = [
        "/etc/nagios/plugins.ini",
        "/usr/local/nagios/etc/plugins.ini",
        "/usr/local/etc/nagios/plugins.ini",
        "/etc/opt/nagios/plugins.ini",
        "/etc/nagios-plugins.ini",
        "/usr/local/etc/nagios-plugins.ini",
        "/etc/opt/nagios-plugins.ini",
    ]

    def __init__(self, section_name=None, config_file=None):
        if not section_name:
            section_name = self.get_default_section_name()
        if not config_file:
            config_file = self.get_default_config_file()
        self.section_name = section_name
        self.config_file = config_file
        self._all_options = self.parse_file(filename=config_file) or {}

    def get_values(self):
        """ Returns a dict with all extra-options with the granted section_name and config_file

        Results are in the form of:
         {
           'key': ["possible","values"]
         }
        """
        return self._all_options.get(self.section_name, {})

    def get_default_section_name(self):
        """ According to extra-opts standard, the default should be filename of check script being run """
        return os.path.basename(sys.argv[0])

    def get_default_config_file(self):
        """ Return path to first readable extra-opt config-file found

        According to the nagiosplugins extra-opts spec the search method is as follows

        1) Search for nagios.ini or nagios-plugins.ini in : splitted variable NAGIOS_CONFIG_PATH
        2) Search in a predefined list of files
        3) Return None if no config file is found

        The method works as follows:

        To quote the spec on NAGIOS_CONFIG_PATH:
            "To use a custom location, set a NAGIOS_CONFIG_PATH environment
            variable to the set of directories that should be checked (this is a
            colon-separated list just like PATH). The first plugins.ini or
            nagios-plugins.ini file found in these directories will be used."

        """
        search_path = []
        nagios_config_path = os.environ.get('NAGIOS_CONFIG_PATH', '')
        for path in nagios_config_path.split(':'):
            search_path.append(os.path.join(path, 'plugins.ini'))
            search_path.append(os.path.join(path, 'nagios-plugins.ini'))

        search_path += self.standard_locations
        self.search_path = search_path
        for path in search_path:
            if os.path.isfile(path):
                return path
        return None

    def get(self, option_name, default=_sentinel):
        """ Return the value of one specific option """
        result = self.getlist(option_name, default)

        # If option was not found, raise error
        if result == _sentinel:
            raise ValueError("Option named %s was not found" % (option_name))
        elif result == default:
            return result
        elif not result:
            # empty list
            return result
        else:
            return result[0]

    def getlist(self, option_name, default=_sentinel):
        """ Return a list of all values for option_name """
        result = self.get_values().get(option_name, default)
        if result == _sentinel:
            raise ValueError("Option named %s was not found" % (option_name))
        return result

    def parse_file(self, filename):
        """ Parses an ini-file and returns a dict of the ini values.


         The datatype returned is a list of sections where each section is a dict of values.

         Example the following the file:
            [main]
            name = this is a name
            key = value
            key = value2

         Would return:
           [
            {'main':
                {
                    'name': ['this is a name'],
                    'key': [value, value2]
                }
            },
            ]

        """
        if filename is None:
            return {}

        f = open(filename)
        try:
            data = f.read()
            return self.parse_string(data)
        finally:
            f.close()


    def parse_string(self, string):
        """ Parsers a string that is supposed to be ini-style format. See parse_file() for more ifno
        """
        sections = {}
        # When parsing inside a section, the name of it stored here.
        section_name = None
        current_section = pynag.Utils.defaultdict(dict)

        for line_no, line, in enumerate(string.splitlines()):
            line = line.strip()

            # skip empty lines
            if not line or line[0] in ('#', ';'):
                continue

            # Check if this is a new section
            if line.startswith('[') and line.endswith(']'):
                section_name = line.strip('[').strip(']').strip()
                current_section = pynag.Utils.defaultdict(list)
                sections[section_name] = current_section
                continue

            # All entries should have key=value format
            if not '=' in line:
                error = "Line %s should be in the form of key=value format (got '%s' instead)" % (line_no, line)
                raise ParserError(error)

            # If we reach here, we parse current line into key and a value section
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            sections[section_name][key].append(value)
        return sections
