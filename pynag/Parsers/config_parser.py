import os
import re
import sys
import time

import pynag.Utils
from pynag.Utils import paths

# TODO: Raise more specific errors in this module.
from pynag.Parsers.errors import ParserError


class ConfigFileNotFound(ParserError):
    """ This exception is thrown if we cannot locate any nagios.cfg-style config file. """


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

        Returns:

            str. Path to the nagios binary

            None if could not find a binary in any of those locations
        """

        for i in paths.BINARY_NAMES:
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

        Returns:

            str. Path to the nagios.cfg or equivalent file

            None if couldn't find a file in any of these locations.
        """
        for file_path in paths.COMMON_CONFIG_FILE_LOCATIONS:
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
            >>> c = Config()
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

            >>> c = Config(cfg_file="/etc/nagios/nagios.cfg")
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
