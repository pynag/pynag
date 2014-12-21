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
import pynag.errors
import pynag.Parsers.errors

import StringIO
import tarfile


# The following imports are for backwards compatibility only. See also bottom of file
from pynag.Parsers.errors import ParserError
from pynag.Parsers import livestatus
from pynag.Parsers import multisite
from pynag.Parsers import extra_opts
from pynag.Parsers import retention_dat
from pynag.Parsers import status_dat
from pynag.Parsers import config_parser
from pynag.Parsers import object_cache
from pynag.Parsers import logs
from pynag.Parsers import ssh_config

_sentinel = object()


Livestatus = livestatus.Livestatus
LivestatusQuery = livestatus.LivestatusQuery
mk_livestatus = livestatus.Livestatus

MultiSite = multisite.MultiSite

LivestatusError = livestatus.LivestatusError
InvalidResponseFromLivestatus = livestatus.InvalidResponseFromLivestatus
LivestatusNotConfiguredException = livestatus.LivestatusNotConfiguredException

ExtraOptsParser = extra_opts.ExtraOptsParser

Config = config_parser.Config
config = config_parser.Config


RetentionDat = retention_dat.RetentionDat
retention = retention_dat.RetentionDat

StatusDat = status_dat.StatusDat
status = status_dat.StatusDat

ObjectCache = object_cache.ObjectCache
object_cache = object_cache.ObjectCache

LogFiles = logs.LogFiles

SshConfig = ssh_config.SshConfig