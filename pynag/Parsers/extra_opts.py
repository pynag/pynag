# -*- coding: utf-8 -*-
"""Module for parsing Nagios 'Extra opts' files."""

from __future__ import absolute_import
import os
import sys

import pynag.Utils

# TODO: Raise more specific errors in this class
from pynag.Parsers.errors import ParserError


_sentinel = object()


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
