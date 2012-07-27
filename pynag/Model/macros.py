# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2010 Pall Sigurdsson
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

"""
This file contains a dict object that maps Nagios Standard macronames to specific values.

i.e. macros['$HOSTADDR$'] should return 'address'
"""

# TODO: This hash map is incomplete, someone should type everything from the documentation to here:
# See: http://nagios.sourceforge.net/docs/3_0/macrolist.html

_standard_macros = {
                   '$HOSTADDRESS$':'address',
                   '$HOSTNAME':'host_name',
                   '$SERVICEDESC':'service_description',
                   }
