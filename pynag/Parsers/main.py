# -*- coding: utf-8 -*-
"""Module for parsing main configuration file (nagios.cfg)."""

from pynag.Utils import paths


class MainConfig(object):
    """ Generic parser for files in the format of key=value.

    This is the format used by nagios.cfg and many other unix configuration files.
    """

    def __init__(self, filename=None):
        if not filename:
            filename = paths.find_main_configuration_file()
        self.filename = filename
        self.data = self.parse()

    def get(self, attribute, default=None):
        """Get the first instance of key."""
        for key, value in self.data:
            if key == attribute:
                return value

    def get_list(self, attribute):
        """Get a list of all values that have attribute_name 'key'."""
        return [value for key, value in self.data if key == attribute]

    @staticmethod
    def _parse_string(string):
        result = []

        for line in string.splitlines():
            # Strip out new line characters
            line = line.strip()

            # Skip blank lines
            if not line:
                continue

            # Skip comments
            if line.startswith("#") or line.startswith(';'):
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            result.append((key, value))
        return result

    def parse(self):
        with open(self.filename) as file_handle:
            data = file_handle.read()
            return self._parse_string(data)
