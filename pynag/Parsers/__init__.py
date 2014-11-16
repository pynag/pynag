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

"""This module contains low-level Parsers for nagios configuration and status objects.

Hint: If you are looking to parse some nagios configuration data, you probably
want pynag.Model module instead.

The highlights of this module are:

class Config: For Parsing nagios local nagios configuration files
class Livestatus: To connect to MK-Livestatus
class StatusDat: To read info from status.dat (not used a lot, migrate to mk-livestatus)
class LogFiles: To read nagios log-files
class MultiSite: To talk with multiple Livestatus instances
"""
import os
import re
import time
import sys
import socket  # for mk_livestatus
import stat

import pynag.Plugins
import pynag.Utils
import StringIO
import tarfile

_sentinel = object()


class Config(object):

    """ Parse and write nagios config files """
    # Regex for beginning of object definition
    # We want everything that matches:
    # define <object_type> {
    __beginning_of_object = re.compile("^\s*define\s+(\w+)\s*\{?(.*)$")

    def __init__(self, cfg_file=None, strict=False):
        """ Constructor for :py:class:`pynag.Parsers.config` class

        Args:

            cfg_file (str): Full path to nagios.cfg. If None, try to
            auto-discover location

            strict (bool): if True, use stricter parsing which is more prone to
            raising exceptions
        """

        self.cfg_file = cfg_file  # Main configuration file
        self.strict = strict  # Use strict parsing or not

        # If nagios.cfg is not set, lets do some minor autodiscover.
        if self.cfg_file is None:
            self.cfg_file = self.guess_cfg_file()

        self.data = {}
        self.maincfg_values = []
        self._is_dirty = False
        self.reset()  # Initilize misc member variables

    def guess_nagios_directory(self):
        """ Returns a path to the nagios configuration directory on your system

        Use this function for determining the nagios config directory in your
        code

        Returns:

            str. directory containing the nagios.cfg file

        Raises:

            :py:class:`pynag.Parsers.ConfigFileNotFound` if cannot guess config
            file location.
        """
        cfg_file = self.guess_cfg_file()
        if not cfg_file:
            raise ConfigFileNotFound("Could not find nagios.cfg")
        return os.path.dirname(cfg_file)

    def guess_nagios_binary(self):
        """ Returns a path to any nagios binary found on your system

        Use this function if you don't want specify path to the nagios binary
        in your code and you are confident that it is located in a common
        location

        Checked locations are as follows:

        * /usr/bin/nagios
        * /usr/sbin/nagios
        * /usr/local/nagios/bin/nagios
        * /nagios/bin/nagios
        * /usr/bin/icinga
        * /usr/sbin/icinga
        * /usr/bin/naemon
        * /usr/sbin/naemon
        * /usr/local/naemon/bin/naemon.cfg
        * /usr/bin/shinken
        * /usr/sbin/shinken

        Returns:

            str. Path to the nagios binary

            None if could not find a binary in any of those locations
        """

        possible_files = ('/usr/bin/nagios',
                          '/usr/sbin/nagios',
                          '/usr/local/nagios/bin/nagios',
                          '/nagios/bin/nagios',
                          '/usr/bin/icinga',
                          '/usr/sbin/icinga',
                          '/usr/bin/naemon',
                          '/usr/sbin/naemon',
                          '/usr/local/naemon/bin/naemon.cfg',
                          '/usr/bin/shinken',
                          '/usr/sbin/shinken')

        possible_binaries = ('nagios', 'nagios3', 'naemon', 'icinga', 'shinken')
        for i in possible_binaries:
            command = ['which', i]
            code, stdout, stderr = pynag.Utils.runCommand(command=command, shell=False)
            if code == 0:
                return stdout.splitlines()[0].strip()

        return None

    def guess_cfg_file(self):
        """ Returns a path to any nagios.cfg found on your system

        Use this function if you don't want specify path to nagios.cfg in your
        code and you are confident that it is located in a common location

        Checked locations are as follows:

        * /etc/nagios/nagios.cfg
        * /etc/nagios3/nagios.cfg
        * /usr/local/nagios/etc/nagios.cfg
        * /nagios/etc/nagios/nagios.cfg
        * ./nagios.cfg
        * ./nagios/nagios.cfg
        * /etc/icinga/icinga.cfg
        * /usr/local/icinga/etc/icinga.cfg
        * ./icinga.cfg
        * ./icinga/icinga.cfg
        * /etc/naemon/naemon.cfg
        * /usr/local/naemon/etc/naemon.cfg
        * ./naemon.cfg
        * ./naemon/naemon.cfg
        * /etc/shinken/shinken.cfg

        Returns:

            str. Path to the nagios.cfg or equivalent file

            None if couldn't find a file in any of these locations.
        """

        possible_files = ('/etc/nagios/nagios.cfg',
                          '/etc/nagios3/nagios.cfg',
                          '/usr/local/nagios/etc/nagios.cfg',
                          '/nagios/etc/nagios/nagios.cfg',
                          './nagios.cfg',
                          './nagios/nagios.cfg',
                          '/etc/icinga/icinga.cfg',
                          '/usr/local/icinga/etc/icinga.cfg',
                          './icinga.cfg',
                          './icinga/icinga.cfg',
                          '/etc/naemon/naemon.cfg',
                          '/usr/local/naemon/etc/naemon.cfg',
                          './naemon.cfg',
                          './naemon/naemon.cfg',
                          '/etc/shinken/shinken.cfg',
                          )

        for file_path in possible_files:
            if self.isfile(file_path):
                return file_path
        return None

    def reset(self):
        """ Reinitializes the data of a parser instance to its default values.
        """

        self.cfg_files = []  # List of other configuration files
        self.data = {}  # dict of every known object definition
        self.errors = []  # List of ParserErrors
        self.item_list = None
        self.item_cache = None
        self.maincfg_values = []  # The contents of main nagios.cfg
        self._resource_values = []  # The contents of any resource_files
        self.item_apply_cache = {}  # This is performance tweak used by _apply_template

        # This is a pure listof all the key/values in the config files.  It
        # shouldn't be useful until the items in it are parsed through with the proper
        # 'use' relationships
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
        """ Determine if an item has a template associated with it

        Args:
            target (dict): Parsed item as parsed by :py:class:`pynag.Parsers.config`
        """
        return 'use' in target

    def _get_pid(self):
        """ Checks the lock_file var in nagios.cfg and returns the pid from the file

        If the pid file does not exist, returns None.
        """
        try:
            return self.open(self.get_cfg_value('lock_file'), "r").readline().strip()
        except Exception:
            return None

    def _get_hostgroup(self, hostgroup_name):
        """ Returns the hostgroup that matches the queried name.

        Args:
            hostgroup_name: Name of the hostgroup to be returned (string)

        Returns:
            Hostgroup item with hostgroup_name that matches the queried name.
        """

        return self.data['all_hostgroup'].get(hostgroup_name, None)

    def _get_key(self, object_type, user_key=None):
        """ Return the correct 'key' for an item.

        This is mainly a helper method for other methods in this class. It is
        used to shorten code repetition.

        Args:

            object_type: Object type from which to obtain the 'key' (string)

            user_key: User defined key. Default None. (string)

        Returns:
            Correct 'key' for the object type. (string)
        """

        if not user_key and not object_type in self.object_type_keys:
            raise ParserError("Unknown key for object type:  %s\n" % object_type)

        # Use a default key
        if not user_key:
            user_key = self.object_type_keys[object_type]

        return user_key

    def _get_item(self, item_name, item_type):
        """ Return an item from a list

        Creates a cache of items in self.pre_object_list and returns an element
        from this cache. Looks for an item with corresponding name and type.

        Args:

            item_name: Name of the item to be returned (string)

            item_type: Type of the item to be returned (string)

        Returns:

            Item with matching name and type from
            :py:attr:`pynag.Parsers.config.item_cache`
        """
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
        """ Apply all attributes of item named parent_name to "original_item".

        Applies all of the attributes of parents (from the 'use' field) to item.

        Args:

            original_item: Item 'use'-ing a parent item. The parent's attributes
            will be concretely added to this item.

        Returns:

            original_item to which have been added all the attributes defined
            in parent items.
        """

        # TODO: There is space for more performance tweaks here
        # If item does not inherit from anyone else, lets just return item as is.
        if 'use' not in original_item:
            return original_item
        object_type = original_item['meta']['object_type']
        raw_definition = original_item['meta']['raw_definition']
        my_cache = self.item_apply_cache.get(object_type, {})

        # Performance tweak, if item has been parsed. Lets not do it again
        if raw_definition in my_cache:
            return my_cache[raw_definition]

        parent_names = original_item['use'].split(',')
        parent_items = []
        for parent_name in parent_names:
            parent_item = self._get_item(parent_name, object_type)
            if parent_item is None:
                error_string = "Can not find any %s named %s\n" % (object_type, parent_name)
                self.errors.append(ParserError(error_string, item=original_item))
                continue

            try:
                # Parent item probably has use flags on its own. So lets apply to parent first
                parent_item = self._apply_template(parent_item)
            except RuntimeError:
                t, e = sys.exc_info()[:2]
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
            my_cache[raw_definition] = original_item

        return original_item

    def _get_items_in_file(self, filename):
        """ Return all items in the given file

        Iterates through all elements in self.data and gatehrs all the items
        defined in the queried filename.

        Args:

            filename: file from which are defined the items that will be
            returned.

        Returns:

            A list containing all the items in self.data that were defined in
            filename
        """
        return_list = []

        for k in self.data.keys():
            for item in self[k]:
                if item['meta']['filename'] == filename:
                    return_list.append(item)
        return return_list

    def get_new_item(self, object_type, filename):
        """ Returns an empty item with all necessary metadata

        Creates a new item dict and fills it with usual metadata:

            * object_type : object_type (arg)
            * filename : filename (arg)
            * template_fields = []
            * needs_commit = None
            * delete_me = None
            * defined_attributes = {}
            * inherited_attributes = {}
            * raw_definition = "define %s {\\n\\n} % object_type"

        Args:

            object_type: type of the object to be created (string)

            filename: Path to which the item will be saved (string)

        Returns:

            A new item with default metadata

        """

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
        """ Parses filename with self.parse_filename and append results in self._pre_object_list

        This function is mostly here for backwards compatibility

        Args:

            filename: the file to be parsed. This is supposed to a nagios object definition file
        """
        for i in self.parse_file(filename):
            self.pre_object_list.append(i)

    def parse_file(self, filename):
        """ Parses a nagios object configuration file and returns lists of dictionaries.

        This is more or less a wrapper around :py:meth:`config.parse_string`,
        so reading documentation there is useful.

        Args:

            filename: Path to the file to parse (string)

        Returns:

            A list containing elements parsed by :py:meth:`parse_string`
        """
        try:
            raw_string = self.open(filename, 'rb').read()
            return self.parse_string(raw_string, filename=filename)
        except IOError:
            t, e = sys.exc_info()[:2]
            parser_error = ParserError(e.strerror)
            parser_error.filename = e.filename
            self.errors.append(parser_error)
            return []

    def parse_string(self, string, filename='None'):
        """ Parses a string, and returns all object definitions in that string

        Args:

            string: A string containing one or more object definitions

            filename (optional): If filename is provided, it will be referenced
            when raising exceptions

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

        Raises:

            :py:class:`ParserError`

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

            # Cleanup and line skips
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

                # Destroy the Nagios Object
                current = None
                continue

            elif line.startswith('define'):  # beginning of object definition
                if in_definition:
                    msg = "Unexpected 'define' in {filename} on line {line_num}. was expecting '}}'."
                    msg = msg.format(**locals())
                    self.errors.append(ParserError(msg, item=current))

                m = self.__beginning_of_object.search(line)

                tmp_buffer = [line]
                object_type = m.groups()[0]
                if self.strict and object_type not in self.object_type_keys.keys():
                    raise ParserError(
                        "Don't know any object definition of type '%s'. it is not in a list of known object definitions." % object_type)
                current = self.get_new_item(object_type, filename)
                current['meta']['line_start'] = line_num

                # Start off an object
                in_definition = True

                # Looks to me like nagios ignores everything after the {, so why shouldn't we ?
                rest = m.groups()[1]
                continue
            else:  # In the middle of an object definition
                tmp_buffer.append('    ' + line)

            # save whatever's left in the buffer for the next iteration
            if not in_definition:
                append = line
                continue

            # this is an attribute inside an object definition
            if in_definition:
                #(key, value) = line.split(None, 1)
                tmp = line.split(None, 1)
                if len(tmp) > 1:
                    (key, value) = tmp
                else:
                    key = tmp[0]
                    value = ""

                # Strip out in-line comments
                if value.find(";") != -1:
                    value = value.split(";", 1)[0]

                # Clean info
                key = key.strip()
                value = value.strip()

                # Rename some old values that may be in the configuration
                # This can probably be removed in the future to increase performance
                if (current['meta']['object_type'] == 'service') and key == 'description':
                    key = 'service_description'

                # Special hack for timeperiods as they are not consistent with other objects
                # We will treat whole line as a key with an empty value
                if (current['meta']['object_type'] == 'timeperiod') and key not in ('timeperiod_name', 'alias'):
                    key = line
                    value = ''
                current[key] = value
                current['meta']['defined_attributes'][key] = value
            # Something is wrong in the config
            else:
                raise ParserError("Error: Unexpected token in file '%s'" % filename)

        # Something is wrong in the config
        if in_definition:
            raise ParserError("Error: Unexpected EOF in file '%s'" % filename)

        return result

    def _locate_item(self, item):
        """ This is a helper function for anyone who wishes to modify objects.

        It takes "item", locates the file which is configured in, and locates
        exactly the lines which contain that definition.

        Returns: (tuple)

            (everything_before, object_definition, everything_after, filename):

                * everything_before (list of lines): Every line in filename before object was defined
                * everything_after (list of lines): Every line in "filename" after object was defined
                * object_definition (list of lines): Every line used to define our item in "filename"
                * filename (string): file in which the object was written to

        Raises:

            :py:class:`ValueError` if object was not found in "filename"

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
        my_file = self.open(filename)
        all_lines = my_file.readlines()
        my_file.close()

        start = my_item['meta']['line_start'] - 1
        end = my_item['meta']['line_end']
        everything_before = all_lines[:start]
        object_definition = all_lines[start:end]
        everything_after = all_lines[end:]

        # If there happen to be line continuations in the object we will edit
        # We will remove them from object_definition
        object_definition = self._clean_backslashes(object_definition)
        return everything_before, object_definition, everything_after, filename

    def _clean_backslashes(self, list_of_strings):
        """ Returns list_of_strings with all all strings joined that ended with backslashes

            Args:
                list_of_strings: List of strings to join
            Returns:
                Another list of strings, which lines ending with \ joined together.

        """
        tmp_buffer = ''
        result = []
        for i in list_of_strings:
            if i.endswith('\\\n'):
                tmp_buffer += i.strip('\\\n')
            else:
                result.append(tmp_buffer + i)
                tmp_buffer = ''
        return result

    def _modify_object(self, item, field_name=None, new_value=None, new_field_name=None, new_item=None,
                       make_comments=False):
        """ Locates "item" and changes the line which contains field_name.

        Helper function for object_* functions. Locates "item" and changes the
        line which contains field_name. If new_value and new_field_name are both
        None, the attribute is removed.

        Args:

            item(dict): The item to be modified

            field_name(str): The field_name to modify (if any)

            new_field_name(str): If set, field_name will be renamed

            new_value(str): If set the value of field_name will be changed

            new_item(str): If set, whole object will be replaced with this
            string

            make_comments: If set, put pynag-branded comments where changes
            have been made

        Returns:

            True on success

        Raises:

            :py:class:`ValueError` if object or field_name is not found

            :py:class:`IOError` is save is unsuccessful.

        """
        if item is None:
            return
        if field_name is None and new_item is None:
            raise ValueError("either field_name or new_item must be set")
        if '\n' in str(new_value):
            raise ValueError("Invalid character \\n used as an attribute value.")
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

    def open(self, filename, *args, **kwargs):
        """ Wrapper around global open()

        Simply calls global open(filename, *args, **kwargs) and passes all arguments
        as they are received. See global open() function for more details.
        """
        return open(filename, *args, **kwargs)

    @pynag.Utils.synchronized(pynag.Utils.rlock)
    def write(self, filename, string):
        """ Wrapper around open(filename).write()

        Writes string to filename and closes the file handler. File handler is
        openned in `'w'` mode.

        Args:

            filename: File where *string* will be written. This is the path to
            the file. (string)

            string: String to be written to file. (string)

        Returns:

            Return code as returned by :py:meth:`os.write`

        """
        fh = self.open(filename, 'w')
        return_code = fh.write(string)
        fh.flush()
        # os.fsync(fh)
        fh.close()
        self._is_dirty = True
        return return_code

    def item_rewrite(self, item, str_new_item):
        """ Completely rewrites item with string provided.

        Args:

            item: Item that is to be rewritten

            str_new_item: str representation of the new item

        ..
            In the following line, every "\\n" is actually a simple line break
            This is only a little patch for the generated documentation.

        Examples::
            item_rewrite( item, "define service {\\n name example-service \\n register 0 \\n }\\n" )

        Returns:

            True on success

        Raises:

            :py:class:`ValueError` if object is not found

            :py:class:`IOError` if save fails
        """
        return self._modify_object(item=item, new_item=str_new_item)

    def item_remove(self, item):
        """ Delete one specific item from its configuration files

        Args:

            item: Item that is to be rewritten

            str_new_item: string representation of the new item

        ..
            In the following line, every "\\n" is actually a simple line break
            This is only a little patch for the generated documentation.

        Examples::
            item_remove( item, "define service {\\n name example-service \\n register 0 \\n }\\n" )

        Returns:

            True on success

        Raises:

            :py:class:`ValueError` if object is not found

            :py:class:`IOError` if save fails
        """
        return self._modify_object(item=item, new_item="")

    def item_edit_field(self, item, field_name, new_value):
        """ Modifies one field of a (currently existing) object.

        Changes are immediate (i.e. there is no commit)

        Args:

            item: Item to be modified. Its field `field_name` will be set to
            `new_value`.

            field_name: Name of the field that will be modified. (str)

            new_value: Value to which will be set the field `field_name`. (str)

        Example usage::
            edit_object( item, field_name="host_name", new_value="examplehost.example.com") # doctest: +SKIP

        Returns:
            True on success

        Raises:

            :py:class:`ValueError` if object is not found

            :py:class:`IOError` if save fails
        """
        return self._modify_object(item, field_name=field_name, new_value=new_value)

    def item_remove_field(self, item, field_name):
        """ Removes one field of a (currently existing) object.

        Changes are immediate (i.e. there is no commit)

        Args:

            item: Item to remove field from.

            field_name: Field to remove. (string)

        Example usage::
            item_remove_field( item, field_name="contactgroups" )

        Returns:
            True on success

        Raises:

            :py:class:`ValueError` if object is not found

            :py:class:`IOError` if save fails
        """
        return self._modify_object(item=item, field_name=field_name, new_value=None, new_field_name=None)

    def item_rename_field(self, item, old_field_name, new_field_name):
        """ Renames a field of a (currently existing) item.

        Changes are immediate (i.e. there is no commit).

        Args:

            item: Item to modify.

            old_field_name: Name of the field that will have its name changed. (string)

            new_field_name: New name given to `old_field_name` (string)

        Example usage::
            item_rename_field(item, old_field_name="normal_check_interval", new_field_name="check_interval")

        Returns:
            True on success

        Raises:

            :py:class:`ValueError` if object is not found

            :py:class:`IOError` if save fails
        """
        return self._modify_object(item=item, field_name=old_field_name, new_field_name=new_field_name)

    def item_add(self, item, filename):
        """ Adds a new object to a specified config file.

        Args:

            item: Item to be created

            filename: Filename that we are supposed to write the new item to.
            This is the path to the file. (string)

        Returns:

            True on success

        Raises:

            :py:class:`IOError` on failed save
        """
        if not 'meta' in item:
            item['meta'] = {}
        item['meta']['filename'] = filename

        # Create directory if it does not already exist
        dirname = os.path.dirname(filename)
        if not self.isdir(dirname):
            os.makedirs(dirname)

        str_buffer = self.print_conf(item)
        fh = self.open(filename, 'a')
        fh.write(str_buffer)
        fh.close()
        return True

    def edit_object(self, item, field_name, new_value):
        """ Modifies a (currently existing) item.

        Changes are immediate (i.e. there is no commit)

        Args:

            item: Item to modify.

            field_name: Field that will be updated.

            new_value: Updated value of field `field_name`

        Example Usage:
            edit_object( item, field_name="host_name", new_value="examplehost.example.com")

        Returns:
            True on success

        .. WARNING::

            THIS FUNCTION IS DEPRECATED. USE item_edit_field() instead
        """
        return self.item_edit_field(item=item, field_name=field_name, new_value=new_value)

    def compareObjects(self, item1, item2):
        """ Compares two items. Returns true if they are equal

        Compares every key: value pair for both items. If anything is different,
        the items will not be considered equal.

        Args:
            item1, item2: Items to be compared.

        Returns:

            True -- Items are equal

            False -- Items are not equal
        """
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
        if result is False:
            return False
        return True

    def edit_service(self, target_host, service_description, field_name, new_value):
        """ Edit a service's attributes

        Takes a host, service_description pair to identify the service to modify
        and sets its field `field_name` to `new_value`.

        Args:

            target_host: name of the host to which the service is attached to. (string)

            service_description: Service description of the service to modify. (string)

            field_name: Field to modify. (string)

            new_value: Value to which the `field_name` field will be updated (string)

        Returns:

            True on success

        Raises:

            :py:class:`ParserError` if the service is not found
        """

        original_object = self.get_service(target_host, service_description)
        if original_object is None:
            raise ParserError("Service not found")
        return self.edit_object(original_object, field_name, new_value)

    def _get_list(self, item, key):
        """ Return a comma list from an item

        Args:

            item: Item from which to select value. (string)

            key: Field name of the value to select and return as a list. (string)

        Example::

            _get_list(Foo_object, host_name)

            define service {
                service_description Foo
                host_name            larry,curly,moe
            }

            returns
            ['larry','curly','moe']

        Returns:

            A list of the item's values of `key`

        Raises:

            :py:class:`ParserError` if item is not a dict
        """
        if not isinstance(item, dict):
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

        # Alphabetize
        return_list.sort()

        return return_list

    def delete_object(self, object_type, object_name, user_key=None):
        """ Delete object from configuration files

        Args:

            object_type: Type of the object to delete from configuration files.

            object_name: Name of the object to delete from configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            True on success.

        """
        item = self.get_object(object_type=object_type, object_name=object_name, user_key=user_key)
        return self.item_remove(item)

    def delete_service(self, service_description, host_name):
        """ Delete service from configuration files

        Args:

            service_description: service_description field value of the object
            to delete from configuration files.

            host_name: host_name field value of the object to delete from
            configuration files.

        Returns:

            True on success.

        """
        item = self.get_service(host_name, service_description)
        return self.item_remove(item)

    def delete_host(self, object_name, user_key=None):
        """ Delete a host from its configuration files

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            True on success.

        """

        return self.delete_object('host', object_name, user_key=user_key)

    def delete_hostgroup(self, object_name, user_key=None):
        """ Delete a hostgroup from its configuration files

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            True on success.

        """
        return self.delete_object('hostgroup', object_name, user_key=user_key)

    def get_object(self, object_type, object_name, user_key=None):
        """ Return a complete object dictionary

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: User defined key. Default None. (string)

        Returns:

            The item found to match all the criterias.

            None if object is not found

        """
        object_key = self._get_key(object_type, user_key)
        for item in self.data['all_%s' % object_type]:
            if item.get(object_key, None) == object_name:
                return item
        return None

    def get_host(self, object_name, user_key=None):
        """ Return a host object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """

        return self.get_object('host', object_name, user_key=user_key)

    def get_servicegroup(self, object_name, user_key=None):
        """ Return a Servicegroup object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('servicegroup', object_name, user_key=user_key)

    def get_contact(self, object_name, user_key=None):
        """ Return a Contact object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('contact', object_name, user_key=user_key)

    def get_contactgroup(self, object_name, user_key=None):
        """ Return a Contactgroup object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('contactgroup', object_name, user_key=user_key)

    def get_timeperiod(self, object_name, user_key=None):
        """ Return a Timeperiod object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('timeperiod', object_name, user_key=user_key)

    def get_command(self, object_name, user_key=None):
        """ Return a Command object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('command', object_name, user_key=user_key)

    def get_hostgroup(self, object_name, user_key=None):
        """ Return a hostgroup object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('hostgroup', object_name, user_key=user_key)

    def get_servicedependency(self, object_name, user_key=None):
        """ Return a servicedependency object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('servicedependency', object_name, user_key=user_key)

    def get_hostdependency(self, object_name, user_key=None):
        """ Return a hostdependency object

        Args:

            object_name: object_name field value of the object to delete from
            configuration files.

            user_key: user_key to pass to :py:meth:`get_object`

        Returns:

            The item found to match all the criterias.

        """
        return self.get_object('hostdependency', object_name, user_key=user_key)

    def get_service(self, target_host, service_description):
        """ Return a service object

        Args:

            target_host: host_name field of the service to be returned. This is
            the host to which is attached the service.

            service_description: service_description field of the service to be
            returned.

        Returns:

            The item found to match all the criterias.

        """
        for item in self.data['all_service']:
            if item.get('service_description') == service_description and item.get('host_name') == target_host:
                return item
        return None

    def _append_use(self, source_item, name):
        """ Append attributes to source_item that are inherited via 'use' attribute'

        Args:

            source_item: item (dict) to apply the inheritance upon

            name: obsolete (discovered automatically via source_item['use'].
            Here for compatibility.

        Returns:

            Source Item with appended attributes.

        Raises:

            :py:class:`ParserError` on recursion errors

        """
        # Remove the 'use' key
        if "use" in source_item:
            del source_item['use']

        for possible_item in self.pre_object_list:
            if "name" in possible_item:
                # Start appending to the item
                for k, v in possible_item.iteritems():

                    try:
                        if k == 'use':
                            source_item = self._append_use(source_item, v)
                    except Exception:
                        raise ParserError("Recursion error on %s %s" % (source_item, v))

                    # Only add the item if it doesn't already exist
                    if not k in source_item:
                        source_item[k] = v
        return source_item

    def _post_parse(self):
        """ Creates a few optimization tweaks and easy access lists in self.data

        Creates :py:attr:`config.item_apply_cache` and fills the all_object
        item lists in self.data.

        """
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
            # Add the items to the class lists.
        for list_item in self.post_object_list:
            type_list_name = "all_%s" % list_item['meta']['object_type']
            if not type_list_name in self.data:
                self.data[type_list_name] = []

            self.data[type_list_name].append(list_item)

    def commit(self):
        """ Write any changes that have been made to it's appropriate file """
        # Loops through ALL items
        for k in self.data.keys():
            for item in self[k]:

                # If the object needs committing, commit it!
                if item['meta']['needs_commit']:
                    # Create file contents as an empty string
                    file_contents = ""

                    # find any other items that may share this config file
                    extra_items = self._get_items_in_file(item['meta']['filename'])
                    if len(extra_items) > 0:
                        for commit_item in extra_items:
                            # Ignore files that are already set to be deleted:w
                            if commit_item['meta']['delete_me']:
                                continue
                                # Make sure we aren't adding this thing twice
                            if item != commit_item:
                                file_contents += self.print_conf(commit_item)

                    # This is the actual item that needs commiting
                    if not item['meta']['delete_me']:
                        file_contents += self.print_conf(item)

                    # Write the file
                    filename = item['meta']['filename']
                    self.write(filename, file_contents)

                    # Recreate the item entry without the commit flag
                    self.data[k].remove(item)
                    item['meta']['needs_commit'] = None
                    self.data[k].append(item)

    def flag_all_commit(self):
        """ Flag every item in the configuration to be committed
        This should probably only be used for debugging purposes
        """
        for object_type in self.data.keys():
            for item in self.data[object_type]:
                item['meta']['needs_commit'] = True

    def print_conf(self, item):
        """ Return a string that can be used in a configuration file

        Args:

            item: Item to be dumped as a string.

        Returns:

            String representation of item.
        """
        output = ""
        # Header, to go on all files
        output += "# Configuration file %s\n" % item['meta']['filename']
        output += "# Edited by PyNag on %s\n" % time.ctime()

        # Some hostgroup information
        if "hostgroup_list" in item['meta']:
            output += "# Hostgroups: %s\n" % ",".join(item['meta']['hostgroup_list'])

        # Some hostgroup information
        if "service_list" in item['meta']:
            output += "# Services: %s\n" % ",".join(item['meta']['service_list'])

        # Some hostgroup information
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
        """ Load a general config file (like nagios.cfg) that has key=value config file format. Ignore comments

        Arguments:

            filename: name of file to parse, if none nagios.cfg will be used

        Returns:

            a [ (key,value), (key,value) ] list
        """
        result = []
        if not filename:
            filename = self.cfg_file
        for line in self.open(filename).readlines():
            # Strip out new line characters
            line = line.strip()

            # Skip blank lines
            if line == "":
                continue

            # Skip comments
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

            filename: Name of config file that will be edited (i.e. nagios.cfg)

            attribute: name of attribute to edit (i.e. check_external_commands)

            new_value: new value for the said attribute (i.e. "1"). None deletes
            the line.

            old_value: Useful if multiple attributes exist (i.e. cfg_dir) and
            you want to replace a specific one.

            append: If true, do not overwrite current setting. Instead append
            this at the end. Use this with settings that are repeated like
            cfg_file.

        Examples::

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

        write_buffer = self.open(filename).readlines()
        is_dirty = False  # dirty if we make any changes
        for i, line in enumerate(write_buffer):
            # Strip out new line characters
            line = line.strip()

            # Skip blank lines
            if line == "":
                continue

            # Skip comments
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
            elif append is False and not old_value:
                write_buffer[i] = new_line
                is_dirty = True
                break
        if is_dirty is False and new_value is not None:
            # If we get here, it means we read the whole file,
            # and we have not yet made any changes, So we assume
            # We should append to the file
            write_buffer.append(new_line)
            is_dirty = True
            # When we get down here, it is time to write changes to file
        if is_dirty is True:
            str_buffer = ''.join(write_buffer)
            self.write(filename, str_buffer)
            return True
        else:
            return False

    def needs_reload(self):
        """  Checks if the Nagios service needs a reload.

        Returns:

            True if Nagios service needs reload of cfg files

            False if reload not needed or Nagios is not running
        """
        if not self.maincfg_values:
            self.reset()
            self.parse_maincfg()
        new_timestamps = self.get_timestamps()
        object_cache_file = self.get_cfg_value('object_cache_file')

        if self._get_pid() is None:
            return False
        if not object_cache_file:
            return True
        if not self.isfile(object_cache_file):
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
        """ Checks if the Nagios configuration needs to be reparsed.

        Returns:

            True if any Nagios configuration file has changed since last parse()

        """
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

        This function is mainly used by config.parse() which also parses your
        whole configuration set.

        Raises:

            py:class:`ConfigFileNotFound`

        """
        # If nagios.cfg is not set, lets do some minor autodiscover.
        if self.cfg_file is None:
            raise ConfigFileNotFound('Could not find nagios.cfg')

        self.maincfg_values = self._load_static_file(self.cfg_file)

    @pynag.Utils.synchronized(pynag.Utils.rlock)
    def parse(self):
        """ Parse all objects in your nagios configuration

        This functions starts by loading up your nagios.cfg ( parse_maincfg() )
        then moving on to your object configuration files (as defined via
        cfg_file and cfg_dir) and and your resource_file as well.

        Returns:

          None

        Raises:

          :py:class:`IOError` if unable to read any file due to permission
          problems
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
        except IOError:
            t, e = sys.exc_info()[:2]
            self.errors.append(str(e))

        self.timestamps = self.get_timestamps()

        # This loads everything into
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

            :py:class:`KeyError` if resource is not found

            :py:class:`ParserError` if resource is not found and you do not have
            permissions

        """
        resources = self.get_resources()
        for k, v in resources:
            if k == resource_name:
                return v

    def get_timestamps(self):
        """ Returns hash map of all nagios related files and their timestamps"""
        files = {}
        files[self.cfg_file] = None
        for k, v in self.maincfg_values:
            if k in ('resource_file', 'lock_file', 'object_cache_file'):
                files[v] = None
        for i in self.get_cfg_files():
            files[i] = None
        # Now lets lets get timestamp of every file
        for k, v in files.items():
            if not self.isfile(k):
                continue
            files[k] = self.stat(k).st_mtime
        return files

    def isfile(self, *args, **kwargs):
        """ Wrapper around os.path.isfile """
        return os.path.isfile(*args, **kwargs)

    def isdir(self, *args, **kwargs):
        """ Wrapper around os.path.isdir """
        return os.path.isdir(*args, **kwargs)

    def islink(self, *args, **kwargs):
        """ Wrapper around os.path.islink """
        return os.path.islink(*args, **kwargs)

    def readlink(self, *args, **kwargs):
        """ Wrapper around os.readlink """
        return os.readlink(*args, **kwargs)

    def stat(self, *args, **kwargs):
        """ Wrapper around os.stat """
        return os.stat(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """ Wrapper around os.remove """
        return os.remove(*args, **kwargs)

    def access(self, *args, **kwargs):
        """ Wrapper around os.access """
        return os.access(*args, **kwargs)

    def listdir(self, *args, **kwargs):
        """ Wrapper around os.listdir """

        return os.listdir(*args, **kwargs)

    def exists(self, *args, **kwargs):
        """ Wrapper around os.path.exists """
        return os.path.exists(*args, **kwargs)

    def get_resources(self):
        """Returns a list of every private resources from nagios.cfg"""
        resources = []
        for config_object, config_value in self.maincfg_values:
            if config_object == 'resource_file' and self.isfile(config_value):
                resources += self._load_static_file(config_value)
        return resources

    def extended_parse(self):
        """ This parse is used after the initial parse() command is run.

        It is only needed if you want extended meta information about hosts or other objects
        """
        # Do the initial parsing
        self.parse()

        # First, cycle through the hosts, and append hostgroup information
        index = 0
        for host in self.data['all_host']:
            if host.get("register", None) == "0":
                continue
            if not "host_name" in host:
                continue
            if not "hostgroup_list" in self.data['all_host'][index]['meta']:
                self.data['all_host'][index]['meta']['hostgroup_list'] = []

            # Append any hostgroups that are directly listed in the host definition
            if "hostgroups" in host:
                for hostgroup_name in self._get_list(host, 'hostgroups'):
                    if not "hostgroup_list" in self.data['all_host'][index]['meta']:
                        self.data['all_host'][index]['meta']['hostgroup_list'] = []
                    if hostgroup_name not in self.data['all_host'][index]['meta']['hostgroup_list']:
                        self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup_name)

            # Append any services which reference this host
            service_list = []
            for service in self.data['all_service']:
                if service.get("register", None) == "0":
                    continue
                if not "service_description" in service:
                    continue
                if host['host_name'] in self._get_active_hosts(service):
                    service_list.append(service['service_description'])
            self.data['all_host'][index]['meta']['service_list'] = service_list

            # Increment count
            index += 1

        # Loop through all hostgroups, appending them to their respective hosts
        for hostgroup in self.data['all_hostgroup']:
            for member in self._get_list(hostgroup, 'members'):
                index = 0
                for host in self.data['all_host']:
                    if not "host_name" in host:
                        continue

                    # Skip members that do not match
                    if host['host_name'] == member:

                        # Create the meta var if it doesn' exist
                        if not "hostgroup_list" in self.data['all_host'][index]['meta']:
                            self.data['all_host'][index]['meta']['hostgroup_list'] = []

                        if hostgroup['hostgroup_name'] not in self.data['all_host'][index]['meta']['hostgroup_list']:
                            self.data['all_host'][index]['meta']['hostgroup_list'].append(hostgroup['hostgroup_name'])

                    # Increment count
                    index += 1

        # Expand service membership
        index = 0
        for service in self.data['all_service']:
            # Find a list of hosts to negate from the final list
            self.data['all_service'][index]['meta']['service_members'] = self._get_active_hosts(service)

            # Increment count
            index += 1

    def _get_active_hosts(self, item):
        """ Given an object, return a list of active hosts.

        This will exclude hosts that are negated with a "!"

        Args:

            item: Item to obtain active hosts from.

        Returns:

            List of all the active hosts for `item`
        """
        # First, generate the negation list
        negate_hosts = []

        # Hostgroups
        if "hostgroup_name" in item:
            for hostgroup_name in self._get_list(item, 'hostgroup_name'):
                if hostgroup_name[0] == "!":
                    hostgroup_obj = self.get_hostgroup(hostgroup_name[1:])
                    negate_hosts.extend(self._get_list(hostgroup_obj, 'members'))

        # Host Names
        if "host_name" in item:
            for host_name in self._get_list(item, 'host_name'):
                if host_name[0] == "!":
                    negate_hosts.append(host_name[1:])

        # Now get hosts that are actually listed
        active_hosts = []

        # Hostgroups
        if "hostgroup_name" in item:
            for hostgroup_name in self._get_list(item, 'hostgroup_name'):
                if hostgroup_name[0] != "!":
                    active_hosts.extend(self._get_list(self.get_hostgroup(hostgroup_name), 'members'))

        # Host Names
        if "host_name" in item:
            for host_name in self._get_list(item, 'host_name'):
                if host_name[0] != "!":
                    active_hosts.append(host_name)

        # Combine the lists
        return_hosts = []
        for active_host in active_hosts:
            if active_host not in negate_hosts:
                return_hosts.append(active_host)

        return return_hosts

    def get_cfg_dirs(self):
        """ Parses the main config file for configuration directories

        Returns:

            List of all cfg directories used in this configuration

        Example::

            print(get_cfg_dirs())
            ['/etc/nagios/hosts','/etc/nagios/objects',...]

        """
        cfg_dirs = []
        for config_object, config_value in self.maincfg_values:
            if config_object == "cfg_dir":
                cfg_dirs.append(config_value)
        return cfg_dirs

    def get_cfg_files(self):
        """ Return a list of all cfg files used in this configuration

        Filenames are normalised so that if nagios.cfg specifies relative
        filenames we will convert it to fully qualified filename before returning.

        Returns:

            List of all configurations files used in the configuration.

        Example:

            print(get_cfg_files())
            ['/etc/nagios/hosts/host1.cfg','/etc/nagios/hosts/host2.cfg',...]

        """
        cfg_files = []
        for config_object, config_value in self.maincfg_values:

            # Add cfg_file objects to cfg file list
            if config_object == "cfg_file":
                config_value = self.abspath(config_value)
                if self.isfile(config_value):
                    cfg_files.append(config_value)

            # Parse all files in a cfg directory
            if config_object == "cfg_dir":
                config_value = self.abspath(config_value)
                directories = []
                raw_file_list = []
                directories.append(config_value)
                # Walk through every subdirectory and add to our list
                while directories:
                    current_directory = directories.pop(0)
                    # Nagios doesnt care if cfg_dir exists or not, so why should we ?
                    if not self.isdir(current_directory):
                        continue
                    for item in self.listdir(current_directory):
                        # Append full path to file
                        item = "%s" % (os.path.join(current_directory, item.strip()))
                        if self.islink(item):
                            item = os.readlink(item)
                        if self.isdir(item):
                            directories.append(item)
                        if raw_file_list.count(item) < 1:
                            raw_file_list.append(item)
                for raw_file in raw_file_list:
                    if raw_file.endswith('.cfg'):
                        if self.exists(raw_file) and not self.isdir(raw_file):
                            # Nagios doesnt care if cfg_file exists or not, so we will not throws errors
                            cfg_files.append(raw_file)

        return cfg_files

    def abspath(self, path):
        """ Return the absolute path of a given relative path.

        The current working directory is assumed to be the dirname of nagios.cfg

        Args:

            path: relative path to be transformed into absolute path. (string)

        Returns:

            Absolute path of given relative path.

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
        """ Returns one specific value from your nagios.cfg file,
        None if value is not found.

        Arguments:

            key: what attribute to fetch from nagios.cfg (example: "command_file" )

        Returns:

            String of the first value found for

        Example:

            >>> c = Config() # doctest: +SKIP
            >>> log_file = c.get_cfg_value('log_file') # doctest: +SKIP
            # Should return something like "/var/log/nagios/nagios.log"
        """
        if not self.maincfg_values:
            self.parse_maincfg()
        for k, v in self.maincfg_values:
            if k == key:
                return v
        return None

    def get_object_types(self):
        """ Returns a list of all discovered object types """
        return map(lambda x: re.sub("all_", "", x), self.data.keys())

    def cleanup(self):
        """ Remove configuration files that have no configuration items """
        for filename in self.cfg_files:
            if not self.parse_file(filename):  # parse_file returns empty list on empty files
                self.remove(filename)
                # If nagios.cfg specifies this file directly via cfg_file directive then...
                for k, v in self.maincfg_values:
                    if k == 'cfg_file' and v == filename:
                        self._edit_static_file(k, old_value=v, new_value=None)

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data[key]


class LivestatusQuery(object):
    """Convenience class to help construct a livestatus query."""

    # The following constants describe names of specific
    # Livestatus headers:
    _RESPONSE_HEADER = 'ResponseHeader'
    _OUTPUT_FORMAT = 'OutputFormat'
    _COLUMNS = 'Columns'
    _COLUMN_HEADERS = 'ColumnHeaders'
    _AUTH_USER = 'AuthUser'
    _STATS = 'Stats'
    _FILTER = 'Filter'

    # How a header line is formatted in a query
    _FORMAT_OF_HEADER_LINE = '{keyword}: {arguments}'

    def __init__(self, query, *args, **kwargs):
        """Create a new LivestatusQuery.

        Args:
            query: String. Initial query (like GET hosts)
            *args: String. Any args will appended to the query as additional headers.
            **kwargs: String. Any kwargs will be treated like additional filter to our query.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_query()
            'GET services\\n'

            >>> query = LivestatusQuery('GET services', 'OutputFormat: json')
            >>> query.get_query()
            'GET services\\nOutputFormat: json\\n'

            >>> query = LivestatusQuery('GET services', 'Columns: service_description', host_name='localhost')
            >>> query.get_query()
            'GET services\\nColumns: service_description\\nFilter: host_name = localhost\\n'
        """
        self._query = query.splitlines()
        self._query += pynag.Utils.grep_to_livestatus(*args,**kwargs)

    def get_query(self):
        """Get a string representation of our query

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_query()
            'GET services\\n'
            >>> query.add_header('Filter', 'host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n'

        Returns:
            A string. String representation of our query that is compatibe
            with livestatus.
        """
        return '\n'.join(self._query) + '\n'

    def get_header(self, keyword):
        """Get first header found with keyword in it.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.get_header('OutputFormat')  # Returns None
            >>> query.set_outputformat('python')
            >>> query.get_header('OutputFormat')
            'python'
        """
        signature = keyword + ':'
        for header in self._query:
            if header.startswith(signature):
                argument = header.split(':', 1)[1]
                argument = argument.strip()
                return argument

    def column_headers(self):
        """Check if ColumnHeaders are on or off.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.column_headers() # If not set, they are off
            False
            >>> query.set_columnheaders('on')
            >>> query.column_headers()
            True
        """
        column_headers = self.get_header(self._COLUMN_HEADERS)
        if not column_headers or column_headers == 'off':
            return False
        if column_headers == 'on':
            return True
        raise LivestatusError("Not sure if ColumnHeaders are on or off, got '%s'" % column_headers)

    def output_format(self):
        """Return the currently configured OutputFormat if any is set.

         Examples:
             >>> query = LivestatusQuery('GET services')
             >>> query.output_format()  # Returns None
             >>> query.set_outputformat('python')
             >>> query.output_format()
             'python'
        """
        return self.get_header(self._OUTPUT_FORMAT)

    def add_header_line(self, header_line):
        """Add a new header line to our livestatus query

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.add_header_line('Filter: host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n'
        """
        self._query.append(header_line)

    def add_header(self, keyword, arguments):
        """Add a new header to our livestatus query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.add_header('Filter', 'host_name = foo')
            >>> query.get_query()
            'GET services\\nFilter: host_name = foo\\n'
        """
        header_line = self._FORMAT_OF_HEADER_LINE.format(keyword=keyword, arguments=arguments)
        self.add_header_line(header_line)

    def has_header(self, keyword):
        """ Returns True if specific header is in current query.

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_header('OutputFormat')
            False
            >>> query.add_header('OutputFormat', 'fixed16')
            >>> query.has_header('OutputFormat')
            True

        """
        signature = keyword + ':'
        for row in self._query:
            if row.startswith(signature):
                return True
        return False

    def remove_header(self, keyword):
        """Remove a header from our query

        Examples:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_header('OutputFormat')
            False
            >>> query.add_header('OutputFormat', 'fixed16')
            >>> query.has_header('OutputFormat')
            True
            >>> query.remove_header('OutputFormat')
            >>> query.has_header('OutputFormat')
            False
        """
        signature = keyword + ':'
        self._query = filter(lambda x: not x.startswith(signature), self._query)

    def set_responseheader(self, response_header='fixed16'):
        """Set ResponseHeader to our query.

        Args:
            response_header: String. Response header that livestatus knows. Example: fixed16

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_responseheader()
            >>> query.get_query()
            'GET services\\nResponseHeader: fixed16\\n'
        """
        # First remove whatever responseheader might have been set before
        self.remove_header(self._RESPONSE_HEADER)
        self.add_header(self._RESPONSE_HEADER, response_header)

    def set_outputformat(self, output_format):
        """Set OutFormat header in our query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_outputformat('json')
            >>> query.get_query()
            'GET services\\nOutputFormat: json\\n'
        """
        # Remove outputformat if it was already in out query
        self.remove_header(self._OUTPUT_FORMAT)
        self.add_header(self._OUTPUT_FORMAT, output_format)

    def set_columnheaders(self, status='on'):
        """Turn on or off ColumnHeaders

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_columnheaders('on')
            >>> query.get_query()
            'GET services\\nColumnHeaders: on\\n'
            >>> query.set_columnheaders('off')
            >>> query.get_query()
            'GET services\\nColumnHeaders: off\\n'
        """
        self.remove_header(self._COLUMN_HEADERS)
        self.add_header(self._COLUMN_HEADERS, status)

    def set_authuser(self, auth_user):
        """Set AuthUser in our query.

        Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.set_authuser('nagiosadmin')
            >>> query.get_query()
            'GET services\\nAuthUser: nagiosadmin\\n'
        """
        self.remove_header(self._AUTH_USER)
        self.add_header(self._AUTH_USER, auth_user)

    def has_responseheader(self):
        """ Check if there are any ResponseHeaders set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_responseheader()
            False
            >>> query.set_responseheader('fixed16')
            >>> query.has_responseheader()
            True

        Returns:
            Boolean. True if query has any ResponseHeader, otherwise False.
        """
        return self.has_header(self._RESPONSE_HEADER)

    def has_authuser(self):
        """ Check if AuthUser is set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_authuser()
            False
            >>> query.set_authuser('nagiosadmin')
            >>> query.has_authuser()
            True

        Returns:
            Boolean. True if query has any AuthUser, otherwise False.
        """
        return self.has_header(self._AUTH_USER)

    def has_outputformat(self):
        """ Check if OutputFormat is set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_outputformat()
            False
            >>> query.set_outputformat('python')
            >>> query.has_outputformat()
            True

        Returns:
            Boolean. True if query has any OutputFormat set, otherwise False.
        """
        return self.has_header(self._OUTPUT_FORMAT)

    def has_columnheaders(self):
        """ Check if there are any ColumnHeaders set.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_columnheaders()
            False
            >>> query.set_columnheaders('on')
            >>> query.has_columnheaders()
            True

        Returns:
            Boolean. True if query has any ColumnHeaders, otherwise False.
        """
        return self.has_header(self._COLUMN_HEADERS)

    def has_stats(self):
        """ Returns True if Stats headers are present in our query.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_stats()
            False
            >>> query.add_header('Stats', 'state = 0')
            >>> query.has_stats()
            True

        Returns:
            Boolean. True if query has any stats, otherwise False.
        """
        return self.has_header(self._STATS)

    def has_filters(self):
        """ Returns True if any filters are applied.

         Example:
            >>> query = LivestatusQuery('GET services')
            >>> query.has_filters()
            False
            >>> query.add_header('Filter', 'host_name = localhost')
            >>> query.has_filters()
            True

        Returns:
            Boolean. True if query has any filters, otherwise False.
        """
        return self.has_header(self._FILTER)

    def __str__(self):
        """Wrapper around self.get_query().

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> str(query)
            'GET services\\nColumns: host_name\\n'

        """
        return self.get_query()

    def splitlines(self, *args, **kwargs):
        """ Wrapper around str(self).splitlines().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> query.splitlines()
            ['GET services', 'Columns: host_name']
        """
        querystring = str(self)
        return querystring.splitlines(*args, **kwargs)

    def split(self, *args, **kwargs):
        """ Wrapper around str(self).split().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
            >>> query = LivestatusQuery('GET services', 'Columns: host_name')
            >>> query.split('\\n')
            ['GET services', 'Columns: host_name', '']
        """
        querystring = str(self)
        return querystring.split(*args, **kwargs)

    def strip(self, *args, **kwargs):
        """ Wrapper around str(self).strip().

         This function is here for backwards compatibility because a lot of callers were previously passing
         in strings, but are now passing in LivestatusQuery. For this purpose we behave like a string.

        Example:
           >>> query = LivestatusQuery('GET services')
           >>> str(query)
           'GET services\\n'
           >>> query.strip()
           'GET services'
        """
        return str(self).strip(*args, **kwargs)


class Livestatus(object):

    """ Wrapper around MK-Livestatus

    Example usage::

        s = Livestatus()
        for hostgroup s.get_hostgroups():
            print(hostgroup['name'], hostgroup['num_hosts'])
    """

    def __init__(self, livestatus_socket_path=None, nagios_cfg_file=None, authuser=None):
        """ Initilize a new instance of Livestatus

        Args:

          livestatus_socket_path: Path to livestatus socket (if none specified,
          use one specified in nagios.cfg)

          nagios_cfg_file: Path to your nagios.cfg. If None then try to
          auto-detect

          authuser: If specified. Every data pulled is with the access rights
          of that contact.

        """
        self.nagios_cfg_file = nagios_cfg_file
        self.error = None
        if not livestatus_socket_path:
            c = config(cfg_file=nagios_cfg_file)
            c.parse_maincfg()
            self.nagios_cfg_file = c.cfg_file
            # Look for a broker_module line in the main config and parse its arguments
            # One of the arguments is path to the file socket created
            for k, v in c.maincfg_values:
                if k == 'broker_module' and "livestatus.o" in v:
                    for arg in v.split()[1:]:
                        if arg.startswith('/') or '=' not in arg:
                            livestatus_socket_path = arg
                            break
                    else:
                        # If we get here, then we could not locate a broker_module argument
                        # that looked like a filename
                        msg = "No Livestatus socket defined. Make sure livestatus broker module is loaded."
                        raise ParserError(msg)
        self.livestatus_socket_path = livestatus_socket_path
        self.authuser = authuser

    def test(self, raise_error=True):
        """ Test if connection to livestatus socket is working

        Args:

            raise_error: If set to True, raise exception if test fails,otherwise return False

        Raises:

            ParserError if raise_error == True and connection fails

        Returns:

            True -- Connection is OK
            False -- there are problems and raise_error==False

        """
        try:
            self.query("GET hosts")
        except Exception:
            t, e = sys.exc_info()[:2]
            self.error = e
            if raise_error:
                raise ParserError("got '%s' when testing livestatus socket. error was: '%s'" % (type(e), e))
            else:
                return False
        return True

    def _get_socket(self):
        """ Returns a socket.socket() instance to communicate with livestatus

        Socket might be either unix filesocket or a tcp socket depenging in
        the content of :py:attr:`livestatus_socket_path`

        Returns:

            Socket to livestatus instance (socket.socket)

        Raises:

            :py:class:`LivestatusNotConfiguredException` on failed connection.

            :py:class:`ParserError` If could not parse configured TCP address
            correctly.

        """
        if not self.livestatus_socket_path:
            msg = ("We could not find path to MK livestatus socket file."
                   "Make sure MK livestatus is installed and configured")
            raise LivestatusNotConfiguredException(msg)
        try:
            # If livestatus_socket_path contains a colon, then we assume that
            # it is tcp socket instead of a local filesocket
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
        except IOError:
            t, e = sys.exc_info()[:2]
            msg = "%s while connecting to '%s'. Make sure nagios is running and mk_livestatus loaded."
            raise ParserError(msg % (e, self.livestatus_socket_path))

    def write(self, livestatus_query):
        """ Send a raw livestatus query to livestatus socket.

        Args:
            livestatus_query: String. A query that will written to livestatus socket.

        Returns:
            A string. The result that comes back from our livestatus socket.

        Raises:
            LivestatusError if there is a problem writing to socket.

        """
        # Lets create a socket and see if we can write to it
        livestatus_socket = self._get_socket()
        try:
            livestatus_socket.send(livestatus_query)
            livestatus_socket.shutdown(socket.SHUT_WR)
            filesocket = livestatus_socket.makefile()
            result = filesocket.read()
            return result
        except IOError:
            msg = "Could not write to socket '%s'. Make sure you have the right permissions"
            raise LivestatusError(msg % self.livestatus_socket_path)
        finally:
            livestatus_socket.close()

    def raw_query(self, query, *args, **kwargs):
        """ Perform LQL queries on the livestatus socket.

        Args:
            query: String. Query to be passed to the livestatus socket
            *args: String. Will be appended to query
            **kwargs: String. Will be appended as 'Filter:' to query.
                For example name='foo' will be appended as 'Filter: name = foo'

        In most cases if you already have constructed a livestatus query, you should only
        need the query argument, args and kwargs can be used to assist in constructing the query.

        For example, the following calls all construct equalant queries:
            l = Livestatus()
            l.query('GET status\nColumns: requests\n')
            l.query('GET status'. 'Columns: requests')
            l.query('GET status', Columns:'requests')

        Returns:
            A string. The results that come out of our livestatus socket.

        Raises:
            LivestatusError: If there are problems with talking to socket.
        """
        livestatus_query = LivestatusQuery(query, *args, **kwargs)
        return self.write(str(livestatus_query))

    def _parse_response_header(self, livestatus_response):
        if not livestatus_response:
            raise LivestatusError("Can't parse empty livestatus response")
        rows = livestatus_response.splitlines()
        header = rows.pop(0)
        data = '\n'.join(rows)
        return_code = header.split()[0]
        if not return_code.startswith('2'):
            error_message = header.strip()
            raise LivestatusError("Error '%s' from livestatus: %s" % (return_code, error_message))
        return data

    def query(self, query, *args, **kwargs):
        """ Performs LQL queries on the livestatus socket.

        The following will be added to our query automatically:
            * If AuthUser is not specified, we add self.authuser.
            * If OutputFormat is not specified, we add python.
            * If ResponseHeader is not specified, we add fixed16.
            * If ColumnHeaders are not specified, we turn them on.
            * If Stats are specified, we turn ColumnHeaders off.

        Args:
            query: String. Query to be passed to the livestatus socket
            *args: String. Will be appended to query
            **kwargs: Will be appended as 'Filter:' to query.
                For example name='foo' will be appended as 'Filter: name = foo'

        Returns:
            List of dicts. Every item in the list is a row from livestatus and
                every row is a dictionary where the keys are column names and values
                are columns.
            Example return value:
                [{'host_name': 'localhost', 'service_description':'Ping'},]

        Raises:
            LivestatusError: If there is a problem talking to livestatus socket.
        """
        # columns parameter exists for backwards compatibility only.
        # By default ColumnHeaders are 'on'.
        kwargs.pop('columns', None)

        livestatus_query = LivestatusQuery(query, *args, **kwargs)

        # Implicitly add ResponseHeader if none was specified
        if not livestatus_query.has_responseheader():
            livestatus_query.set_responseheader('fixed16')

        # Implicitly add OutputFormat if none was specified
        if not livestatus_query.has_outputformat():
            livestatus_query.set_outputformat('python')

        # Implicitly turn ColumnHeaders on if none we specified
        if not livestatus_query.has_columnheaders():
            livestatus_query.set_columnheaders('on')

        # Implicitly add AuthUser if one was configured:
        if self.authuser and not livestatus_query.has_authuser():
            livestatus_query.set_authuser(self.authuser)

        # This piece of code is here to workaround a bug in livestatus when
        # query contains 'Stats' and ColumnHeaders are on.
        # * Old behavior: Livestatus turns columnheaders explicitly off.
        # * New behavior: Livestatus gives us headers, but corrupted data.
        #
        # Out of 2 evils we maintain consistency by choosing the older
        # behavior of always turning of columnheaders for Stats.
        if livestatus_query.has_stats():
            livestatus_query.set_columnheaders('off')

        # This is we actually send our query into livestatus. livestatus_response is the raw response
        # from livestatus socket (string):
        livestatus_response = self.raw_query(livestatus_query)

        if not livestatus_response:
            raise InvalidResponseFromLivestatus(query=livestatus_query, response=livestatus_response)

        # Parse the response header from livestatus, will raise an exception if
        # livestatus returned an error:
        response_data = self._parse_response_header(livestatus_response)

        if livestatus_query.output_format() != 'python':
            return response_data

        # Return empty list if we got no results
        if not response_data:
            return []

        try:
            response_data = eval(response_data)
        except Exception:
            raise InvalidResponseFromLivestatus(query=livestatus_query, response=response_data)

        # Usually when we query livestatus we get back a 'list of rows',
        # however Livestatus had a quirk in the past that if there were Stats
        # in the query Instead of returning rows, it would just return a list
        # of stats. For backwards Compatibility we cling on to the old bug, of
        # not returning 'rows' when asking for stats.
        if livestatus_query.has_stats() and len(response_data) == 1:
            return response_data[0]

        # Backwards compatibility. if ColumnHeaders=Off, we return livestatus
        # original format of lists of lists (instead of lists of dicts)
        if not livestatus_query.column_headers():
            return response_data

        column_headers = response_data.pop(0)

        # Lets throw everything into a hashmap before we return
        result = []
        for line in response_data:
            current_row = {}
            for i, value in enumerate(line):
                column_name = column_headers[i]
                current_row[column_name] = value
            result.append(current_row)
        return result

    def get(self, table, *args, **kwargs):
        """ Same as self.query('GET %s' % (table,))

        Extra arguments will be appended to the query.

        Args:

            table: Table from which the data will be retrieved

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Example::

            get('contacts', 'Columns: name alias')

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET %s' % (table,), *args, **kwargs)

    def get_host(self, host_name):
        """ Performs a GET query for a particular host

        This performs::

            '''GET hosts
            Filter: host_name = %s''' % host_name

        Args:

            host_name: name of the host to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hosts', 'Filter: host_name = %s' % host_name)[0]

    def get_service(self, host_name, service_description):
        """ Performs a GET query for a particular service

        This performs::

            '''GET services
            Filter: host_name = %s
            Filter: service_description = %s''' % (host_name, service_description)

        Args:

            host_name: name of the host the target service is attached to.

            service_description: Description of the service to obtain livestatus
            data from.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET services', 'Filter: host_name = %s' % host_name,
                          'Filter: description = %s' % service_description)[0]

    def get_hosts(self, *args, **kwargs):
        """ Performs a GET query for all hosts

        This performs::

            '''GET hosts %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hosts', *args, **kwargs)

    def get_services(self, *args, **kwargs):
        """ Performs a GET query for all services

        This performs::

            '''GET services
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET services', *args, **kwargs)

    def get_hostgroups(self, *args, **kwargs):
        """ Performs a GET query for all hostgroups

        This performs::

            '''GET hostgroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hostgroups', *args, **kwargs)

    def get_servicegroups(self, *args, **kwargs):
        """ Performs a GET query for all servicegroups

        This performs::

            '''GET servicegroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET servicegroups', *args, **kwargs)

    def get_contactgroups(self, *args, **kwargs):
        """ Performs a GET query for all contactgroups

        This performs::

            '''GET contactgroups
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contactgroups', *args, **kwargs)

    def get_contacts(self, *args, **kwargs):
        """ Performs a GET query for all contacts

        This performs::

            '''GET contacts
            %s %s''' % (*args, **kwargs)

        Args:

            args, kwargs: These will be appendend to the end of the query to
            perform additionnal instructions.

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contacts', *args, **kwargs)

    def get_contact(self, contact_name):
        """ Performs a GET query for a particular contact

        This performs::

            '''GET contacts
            Filter: contact_name = %s''' % contact_name

        Args:

            contact_name: name of the contact to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contacts', 'Filter: contact_name = %s' % contact_name)[0]

    def get_servicegroup(self, name):
        """ Performs a GET query for a particular servicegroup

        This performs::

            '''GET servicegroups
            Filter: servicegroup_name = %s''' % servicegroup_name

        Args:

            servicegroup_name: name of the servicegroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET servicegroups', 'Filter: name = %s' % name)[0]

    def get_hostgroup(self, name):
        """ Performs a GET query for a particular hostgroup

        This performs::

            '''GET hostgroups
            Filter: hostgroup_name = %s''' % hostgroup_name

        Args:

            hostgroup_name: name of the hostgroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET hostgroups', 'Filter: name = %s' % name)[0]

    def get_contactgroup(self, name):
        """ Performs a GET query for a particular contactgroup

        This performs::

            '''GET contactgroups
            Filter: contactgroup_name = %s''' % contactgroup_name

        Args:

            contactgroup_name: name of the contactgroup to obtain livestatus data from

        Returns:

            Answer from livestatus in python format.

        """
        return self.query('GET contactgroups', 'Filter: name = %s' % name)[0]


class RetentionDat(object):

    """ Easy way to parse the content of retention.dat

    After calling parse() contents of retention.dat are kept in self.data

    Example Usage::

        r = retention()
        r.parse()
        print r
        print r.data['info']
    """

    def __init__(self, filename=None, cfg_file=None):
        """ Initilize a new instance of retention.dat

        Args (you only need to provide one of these):

            filename: path to your retention.dat file

            cfg_file: path to your nagios.cfg file, path to retention.dat will
            be looked up in this file

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

            :py:class:`ParserError`: if problem arises while reading status.dat

            :py:class:`ParserError`: if status.dat is not found

            :py:class:`IOError`: if status.dat cannot be read
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
            # Cleanup and line skips
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


class StatusDat(RetentionDat):

    """ Easy way to parse status.dat file from nagios

    After calling parse() contents of status.dat are kept in status.data
    Example usage::

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

        Args (you only need to provide one of these):

            filename: path to your status.dat file

            cfg_file: path to your nagios.cfg file, path to status.dat will be
            looked up in this file

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

        Args:

            contact_name: `contact_name` field of the contact's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the contact.

        Raises:

            ValueError if object is not found

        Example:

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

        Args:

            host_name: `host_name` field of the host's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the host.

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

        Args:

            service_name: `service_name` field of the host's status.dat data
            to parse and return as a dict.

        Returns:

            dict derived from status.dat for the service.

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


class ObjectCache(Config):

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
        """ Creates an instance of ParserError

        Args:

            message: Message to be printed by the error

            item: Pynag item who caused the error

        """
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


class ConfigFileNotFound(ParserError):
    """ This exception is thrown if we cannot locate any nagios.cfg-style config file. """


class LivestatusNotConfiguredException(ParserError):
    """ This exception is raised if we tried to autodiscover path to livestatus and failed """


class LivestatusError(ParserError):
    """ Used when we get errors from Livestatus """


class InvalidResponseFromLivestatus(LivestatusError):
    """Used when an unparsable response comes out of livestatus"""
    def __init__(self, query, response, *args, **kwargs):
        self.query = query
        self.response = response

    def __str__(self):
        message = 'Could not parse response from livestatus.\nQuery:{query}\nResponse: {response}'
        return message.format(query=self.query, response=self.response)


class LogFiles(object):

    """ Parses Logfiles defined in nagios.cfg and allows easy access to its content

    Content is stored in python-friendly arrays of dicts. Output should be more
    or less compatible with mk_livestatus log output
    """

    def __init__(self, maincfg=None):
        self.config = config(maincfg)

        self.log_file = self.config.get_cfg_value('log_file')
        self.log_archive_path = self.config.get_cfg_value('log_archive_path')

    def get_log_entries(self, start_time=None, end_time=None, strict=True, search=None, **kwargs):
        """ Get Parsed log entries for given timeperiod.

         Args:
            start_time: unix timestamp. if None, return all entries from today

            end_time: If specified, only fetch log entries older than this (unix
            timestamp)

            strict: If True, only return entries between start_time and
            end_time, if False, then return entries that belong to same log
            files as given timeset

            search: If provided, only return log entries that contain this
            string (case insensitive)

            kwargs: All extra arguments are provided as filter on the log
            entries. f.e. host_name="localhost"

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

        logfiles = self.get_logfiles()
        if 'filename' in kwargs:
            logfiles = filter(lambda x: x == kwargs.get('filename'), logfiles)

        # If start time was provided, skip all files that we last modified
        # before start_time
        if start_time:
            logfiles = filter(lambda x: start_time <= os.stat(x).st_mtime, logfiles)

        # Log entries are returned in ascending order, which is the opposite of
        # what get_logfiles returns.
        logfiles.reverse()

        result = []
        for log_file in logfiles:
            entries = self._parse_log_file(filename=log_file)
            if len(entries) == 0:
                continue
            first_entry = entries[0]
            last_entry = entries[-1]

            if first_entry['time'] > end_time:
                continue
                # If strict, filter entries to only include the ones in the timespan
            if strict is True:
                entries = [x for x in entries if x['time'] >= start_time and x['time'] <= end_time]
                # If search string provided, filter the string
            if search is not None:
                entries = [x for x in entries if x['message'].lower().find(search.lower()) > -1]
            for k, v in kwargs.items():
                entries = [x for x in entries if x.get(k) == v]
            result += entries

            if start_time is None or int(start_time) >= int(first_entry.get('time')):
                continue

        # Now, logfiles should in MOST cases come sorted for us.
        # However we rely on modification time of files and if it is off,
        # We want to make sure log entries are coming in the correct order.
        # The following sort should not impact performance in the typical use case.
        result.sort(key=lambda x: x.get('time'))

        return result

    def get_logfiles(self):
        """ Returns a list with the fullpath to every log file used by nagios.

        Lists are sorted by modification times. Newest logfile is at the front
        of the list so usually nagios.log comes first, followed by archivelogs

        Returns:

            List of strings

        """
        logfiles = []

        for filename in os.listdir(self.log_archive_path):
            full_path = "%s/%s" % (self.log_archive_path, filename)
            logfiles.append(full_path)
        logfiles.append(self.log_file)

        # Sort the logfiles by modification time, newest file at the front
        compare_mtime = lambda a, b: os.stat(a).st_mtime < os.stat(b).st_mtime
        logfiles.sort(key=lambda x: int(os.stat(x).st_mtime))

        # Newest logfiles go to the front of the list
        logfiles.reverse()

        return logfiles

    def get_flap_alerts(self, **kwargs):
        """ Same as :py:meth:`get_log_entries`, except return timeperiod transitions.

        Takes same parameters.
        """
        return self.get_log_entries(class_name="timeperiod transition", **kwargs)

    def get_notifications(self, **kwargs):
        """ Same as :py:meth:`get_log_entries`, except return only notifications.
        Takes same parameters.
        """
        return self.get_log_entries(class_name="notification", **kwargs)

    def get_state_history(self, start_time=None, end_time=None, host_name=None, strict=True, service_description=None):
        """ Returns a list of dicts, with the state history of hosts and services.

        Args:

           start_time: unix timestamp. if None, return all entries from today

           end_time: If specified, only fetch log entries older than this (unix
           timestamp)

           host_name: If provided, only return log entries that contain this
           string (case insensitive)

           service_description: If provided, only return log entries that contain this
           string (case insensitive)

        Returns:

            List of dicts with state history of hosts and services
        """

        log_entries = self.get_log_entries(start_time=start_time, end_time=end_time, strict=strict, class_name='alerts')
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

            if strict is True:
                if start_time is not None and int(start_time) > int(line.get('time')):
                    continue
                if end_time is not None and int(end_time) < int(line.get('time')):
                    continue

            result.append(line)
        return result

    def _parse_log_file(self, filename=None):
        """ Parses one particular nagios logfile into arrays of dicts.

        Args:

            filename: Log file to be parsed. If is None, then log_file from
            nagios.cfg is used.

        Returns:

            A list of dicts containing all data from the log file
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
        """ Parse one particular line in nagios logfile and return a dict.

        Args:

            line: Line of the log file to be parsed.

        Returns:

            dict containing the information from the log file line.
        """
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

    Usage::

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

        Results are in the form of::

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

        According to the nagiosplugins extra-opts spec the search method is as follows:

            1. Search for nagios.ini or nagios-plugins.ini in : splitted variable NAGIOS_CONFIG_PATH
            2. Search in a predefined list of files
            3. Return None if no config file is found

        The method works as follows:

        To quote the spec on NAGIOS_CONFIG_PATH:

            *"To use a custom location, set a NAGIOS_CONFIG_PATH environment
            variable to the set of directories that should be checked (this is a
            colon-separated list just like PATH). The first plugins.ini or
            nagios-plugins.ini file found in these directories will be used."*

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
        """ Return the value of one specific option

        Args:

            option_name: The value set to this option will be returned

        Returns:

            The value of `option_name`

        Raises:

            :py:class:`ValueError` when `option_name` cannot be found in options

        """
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
        """ Return a list of all values for option_name

        Args:

            option_name: All the values set to this option will be returned

        Returns:

            List containing all the options set to `option_name`

        Raises:

            :py:class:`ValueError` when `option_name` cannot be found in options

        """
        result = self.get_values().get(option_name, default)
        if result == _sentinel:
            raise ValueError("Option named %s was not found" % (option_name))
        return result

    def parse_file(self, filename):
        """ Parses an ini-file and returns a dict of the ini values.

        The datatype returned is a list of sections where each section is a
        dict of values.

        Args:

            filename: Full path to the ini-file to be parsed.

        Example the following the file::

            [main]
            name = this is a name
            key = value
            key = value2

        Would return::

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
        """ Parses a string that is supposed to be ini-style format.

        See :py:meth:`parse_file` for more info

        Args:

            string: String to be parsed. Should be in ini-file format.

        Returns:

            Dictionnary containing all the sections of the ini-file and their
            respective data.

        Raises:

            :py:class:`ParserError` when line does not follow the ini format.

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


class SshConfig(Config):

    """ Parse object configuration files from remote host via ssh

    Uses python-paramiko for ssh connections.
    """

    def __init__(self, host, username, password=None, cfg_file=None):
        """ Creates a SshConfig instance

        Args:

            host: Host to connect to

            username: User to connect with

            password: Password for `username`

            cfg_file: Nagios main cfg file
        """
        import paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password)
        self.ftp = self.ssh.open_sftp()

        import cStringIO
        c = cStringIO.StringIO()
        self.tar = tarfile.open(mode='w', fileobj=c)

        self.cached_stats = {}
        super(SshConfig, self).__init__(cfg_file=cfg_file)

    def open(self, filename, *args, **kwargs):
        """ Behaves like file.open only, via ssh connection """
        return self.tar.extractfile(filename)
        tarinfo = self._get_file(filename)
        string = tarinfo.tobuf()
        print string
        return StringIO.StringIO(string)
        return self.tar.extractfile(tarinfo)

    def add_to_tar(self, path):
        """
        """
        print "Taring ", path
        command = "find '{path}' -type f | tar -c -T - --to-stdout --absolute-names"
        command = command.format(path=path)
        print command
        stdin, stdout, stderr = self.ssh.exec_command(command, bufsize=50000)
        tar = tarfile.open(fileobj=stdout, mode='r|')
        if not self.tar:
            self.tar = tar
            # return
        else:
            for i in tar:
                self.tar.addfile(i)

    def is_cached(self, filename):
        if not self.tar:
            return False
        return filename in self.tar.getnames()

    def _get_file(self, filename):
        """ Download filename and return the TarInfo object """
        if filename not in self.tar.getnames():
            self.add_to_tar(filename)
        return self.tar.getmember(filename)

    def get_cfg_files(self):
        cfg_files = []
        for config_object, config_value in self.maincfg_values:

            # Add cfg_file objects to cfg file list
            if config_object == "cfg_file":
                config_value = self.abspath(config_value)
                if self.isfile(config_value):
                    cfg_files.append(config_value)
            elif config_object == "cfg_dir":
                absolut_path = self.abspath(config_value)
                command = "find '%s' -type f -iname \*cfg" % (absolut_path)
                stdin, stdout, stderr = self.ssh.exec_command(command)
                raw_filelist = stdout.read().splitlines()
                cfg_files += raw_filelist
            else:
                continue
            if not self.is_cached(config_value):
                self.add_to_tar(config_value)
        return cfg_files

    def isfile(self, path):
        """ Behaves like os.path.isfile only, via ssh connection """
        try:
            copy = self._get_file(path)
            return copy.isfile()
        except IOError:
            return False

    def isdir(self, path):
        """ Behaves like os.path.isdir only, via ssh connection """
        try:
            file_stat = self.stat(path)
            return stat.S_ISDIR(file_stat.st_mode)
        except IOError:
            return False

    def islink(self, path):
        """ Behaves like os.path.islink only, via ssh connection """
        try:
            file_stat = self.stat(path)
            return stat.S_ISLNK(file_stat.st_mode)
        except IOError:
            return False

    def readlink(self, path):
        """ Behaves like os.readlink only, via ssh connection """
        return self.ftp.readlink(path)

    def stat(self, *args, **kwargs):
        """ Wrapper around os.stat only, via ssh connection """
        path = args[0]
        if not self.is_cached(path):
            self.add_to_tar(path)
        if path not in self.tar.getnames():
            raise IOError("No such file or directory %s" % path)
        member = self.tar.getmember(path)
        member.st_mode = member.mode
        member.st_mtime = member.mtime
        return member

    def access(self, *args, **kwargs):
        """ Wrapper around os.access only, via ssh connection """
        return os.access(*args, **kwargs)

    def exists(self, path):
        """ Wrapper around os.path.exists only, via ssh connection """
        try:
            self.ftp.stat(path)
            return True
        except IOError:
            return False

    def listdir(self, *args, **kwargs):
        """ Wrapper around os.listdir  but via ssh connection """
        stats = self.ftp.listdir_attr(*args, **kwargs)
        for i in stats:
            self.cached_stats[args[0] + "/" + i.filename] = i
        files = map(lambda x: x.filename, stats)
        return files


class MultiSite(Livestatus):

    """ Wrapps around multiple Livesatus instances and aggregates the results
        of queries.

        Example:
            >>> m = MultiSite()
            >>> m.add_backend(path='/var/spool/nagios/livestatus.socket', name='local')
            >>> m.add_backend(path='127.0.0.1:5992', name='remote')
    """

    def __init__(self, *args, **kwargs):
        super(MultiSite, self).__init__(*args, **kwargs)
        self.backends = {}

    def add_backend(self, path, name):
        """ Add a new livestatus backend to this instance.

         Arguments:
            path (str):  Path to file socket or remote address
            name (str):  Friendly shortname for this backend
        """
        backend = Livestatus(
            livestatus_socket_path=path,
            nagios_cfg_file=self.nagios_cfg_file,
            authuser=self.authuser
        )
        self.backends[name] = backend

    def get_backends(self):
        """ Returns a list of mk_livestatus instances

        Returns:
            list. List of mk_livestatus instances
        """
        return self.backends

    def get_backend(self, backend_name):
        """ Return one specific backend that has previously been added
        """
        if not backend_name:
            return self.backends.values()[0]
        try:
            return self.backends[backend_name]
        except KeyError:
            raise ParserError("No backend found with name='%s'" % backend_name)

    def query(self, query, *args, **kwargs):
        """ Behaves like mk_livestatus.query() except results are aggregated from multiple backends

        Arguments:
            backend (str): If specified, fetch only data from this backend (see add_backend())
            *args:         Passed directly to mk_livestatus.query()
            **kwargs:      Passed directly to mk_livestatus.query()
        """
        result = []
        backend = kwargs.pop('backend', None)

        # Special hack, if 'Stats' argument was provided to livestatus
        # We have to maintain compatibility with old versions of livestatus
        # and return single list with all results instead of a list of dicts
        doing_stats = any(map(lambda x: x.startswith('Stats:'), args + (query,)))

        # Iterate though all backends and run the query
        # TODO: Make this multithreaded
        for name, backend_instance in self.backends.items():
            # Skip if a specific backend was requested and this is not it
            if backend and backend != name:
                continue

            query_result = backend_instance.query(query, *args, **kwargs)
            if doing_stats:
                result = self._merge_statistics(result, query_result)
            else:
                for row in query_result:
                    row['backend'] = name
                    result.append(row)

        return result

    def _merge_statistics(self, list1, list2):
        """ Merges multiple livestatus results into one result

        Arguments:
            list1 (list): List of integers
            list2 (list): List of integers

        Returns:
            list. Aggregated results of list1 + list2
        Example:
            >>> result1 = [1,1,1,1]
            >>> result2 = [2,2,2,2]
            >>> MultiSite()._merge_statistics(result1, result2)
            [3, 3, 3, 3]
        """
        if not list1:
            return list2
        if not list2:
            return list1

        number_of_columns = len(list1)
        result = [0] * number_of_columns
        for row in (list1, list2):
            for i, column in enumerate(row):
                result[i] += column
        return result

    def get_host(self, host_name, backend=None):
        """ Same as Livestatus.get_host() """
        backend = self.get_backend(backend)
        return backend.get_host(host_name)

    def get_service(self, host_name, service_description, backend=None):
        """ Same as Livestatus.get_service() """
        backend = self.get_backend(backend)
        return backend.get_service(host_name, service_description)

    def get_contact(self, contact_name, backend=None):
        """ Same as Livestatus.get_contact() """
        backend = self.get_backend(backend)
        return backend.get_contact(contact_name)

    def get_contactgroup(self, contactgroup_name, backend=None):
        """ Same as Livestatus.get_contact() """
        backend = self.get_backend(backend)
        return backend.get_contactgroup(contactgroup_name)

    def get_servicegroup(self, servicegroup_name, backend=None):
        """ Same as Livestatus.get_servicegroup() """
        backend = self.get_backend(backend)
        return backend.get_servicegroup(servicegroup_name)

    def get_hostgroup(self, hostgroup_name, backend=None):
        """ Same as Livestatus.get_hostgroup() """
        backend = self.get_backend(backend)
        return backend.get_hostgroup(hostgroup_name)


class config(Config):

    """ This class is here only for backwards compatibility. Use Config instead. """


class mk_livestatus(Livestatus):

    """ This class is here only for backwards compatibility. Use Livestatus instead. """


class object_cache(ObjectCache):

    """ This class is here only for backwards compatibility. Use ObjectCache instead. """


class status(StatusDat):

    """ This class is here only for backwards compatibility. Use StatusDat instead. """


class retention(RetentionDat):

    """ This class is here only for backwards compatibility. Use RetentionDat instead. """


if __name__ == '__main__':
    import time
    start = time.time()
    ssh = SshConfig(host='status.adagios.org', username='palli')
    ssh.ssh.get_transport().window_size = 3 * 1024 * 1024
    ssh.ssh.get_transport().use_compression()

    # ssh.add_to_tar('/etc/nagios')
    # sys.exit()
    # ssh.ssh.exec_command("/bin/ls")
    print "before reset"
    ssh.parse()
    end = time.time()
    print "duration=", end - start
    bland = ssh.tar.getmember('/etc/nagios/okconfig/hosts/web-servers/bland.is-http.cfg')
    print bland.tobuf()
    sys.exit(0)
    print "ssh up"
    ssh_conn = FastTransport(('status.adagios.org', 22))
    ssh_conn.connect(username='palli')
    ftp = paramiko.SFTPClient.from_transport(ssh_conn)
    print "connected" \
          ""
    ssh.ssh = ssh_conn
    ssh.ftp = ftp
    print "starting parse"
    print "done parsing"
