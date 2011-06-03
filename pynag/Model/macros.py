# -*- coding: utf-8 -*-
#
# Copyright 2010, Pall Sigurdsson <palli@opensource.is>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
This file contains a dict object that maps Nagios Standard macronames to specific values.

i.e. macros['$HOSTADDR$'] should return 'address'
'''

# TODO: This hash map is incomplete, someone should type everything from the documentation to here:
# See: http://nagios.sourceforge.net/docs/3_0/macrolist.html

_standard_macros = {
                   '$HOSTADDRESS$':'address',
                   '$HOSTNAME':'host_name',
                   '$SERVICEDESC':'service_description',
                   }