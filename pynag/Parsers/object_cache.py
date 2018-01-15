# -*- coding: utf-8 -*-
"""Module for parsing and filtering object_cache files."""

from __future__ import absolute_import
from pynag.Parsers import config_parser


class ObjectCache(config_parser.Config):

    """ Loads the configuration as it appears in objects.cache file """

    def get_cfg_files(self):
        for k, v in self.maincfg_values:
            if k == 'object_cache_file':
                return [v]
