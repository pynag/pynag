# -*- coding: utf-8 -*-

"""This package contains low-level objects and parsers.

If you are looking for a high-level way to parse nagios configs,
see pynag.Model instead.

Everything you see in this file is for backwards compatibility only.

"""

from pynag.Parsers import errors
from pynag.Parsers import livestatus
from pynag.Parsers import multisite
from pynag.Parsers import extra_opts
from pynag.Parsers import retention_dat
from pynag.Parsers import status_dat
from pynag.Parsers import config_parser
from pynag.Parsers import object_cache
from pynag.Parsers import logs
from pynag.Parsers import ssh_config


# config_parser.py
Config = config_parser.Config
config = config_parser.Config

# extra_opts.py
ExtraOptsParser = extra_opts.ExtraOptsParser

# errors.py
ParserError = errors.ParserError

# livestatus.py
Livestatus = livestatus.Livestatus
LivestatusQuery = livestatus.LivestatusQuery
mk_livestatus = livestatus.Livestatus
LivestatusError = livestatus.LivestatusError
InvalidResponseFromLivestatus = livestatus.InvalidResponseFromLivestatus
LivestatusNotConfiguredException = livestatus.LivestatusNotConfiguredException

# multisite.py
MultiSite = multisite.MultiSite

# logs.py
LogFiles = logs.LogFiles

# object_cache.py
ObjectCache = object_cache.ObjectCache
object_cache = object_cache.ObjectCache

# retention_dat.py
RetentionDat = retention_dat.RetentionDat
retention = retention_dat.RetentionDat

# ssh_config.py
SshConfig = ssh_config.SshConfig

# status_dat.py
StatusDat = status_dat.StatusDat
status = status_dat.StatusDat
