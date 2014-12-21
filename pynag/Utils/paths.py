# -*- coding: utf-8 -*-
"""Constants and conveniance methods related to paths to config files, and binaries."""

import os


class Error(Exception):
    """Base class for errors in this module."""


class MainConfigNotFound(Error):
    """Raised when config file or socket could not be found."""


COMMON_CONFIG_FILE_LOCATIONS = [
    # nagios
    '/etc/nagios/nagios.cfg',
    '/etc/nagios3/nagios.cfg',
    '/usr/local/nagios/etc/nagios.cfg',
    '/nagios/etc/nagios/nagios.cfg',
    './nagios.cfg',
    './nagios/nagios.cfg',

    # icinga
    '/etc/icinga/icinga.cfg',
    '/usr/local/icinga/etc/icinga.cfg',
    './icinga.cfg',
    './icinga/icinga.cfg',

    # naemon
    '/etc/naemon/naemon.cfg',
    '/usr/local/naemon/etc/naemon.cfg',
    './naemon.cfg',
    './naemon/naemon.cfg',

    # shinken
    '/etc/shinken/shinken.cfg',
]

BINARY_NAMES = ['nagios', 'nagios3', 'naemon', 'icinga', 'shinken']


def find_main_configuration_file():
        """ Returns a path to any nagios.cfg found on your system

        Use this function if you don't want specify path to nagios.cfg in your
        code and you are confident that it is located in a common location

        Returns:
            Path to nagios.cfg or equivalent file (str)

        Raises:
            MainConfigNotFound: If config cannot be located.
        """
        for file_path in COMMON_CONFIG_FILE_LOCATIONS:
            if os.path.isfile(file_path):
                return file_path

        raise MainConfigNotFound()
