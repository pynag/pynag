#!/usr/bin/python
#
# This script looks for files in your configuration that have no objects in them.
#
#
from __future__ import absolute_import
from __future__ import print_function
import os
import pynag.Model

# Load pynag cache
all_objects = pynag.Model.ObjectDefinition.objects.all

for i in pynag.Model.config.get_cfg_files():
    objects = pynag.Model.ObjectDefinition.objects.filter(filename=i)
    if len(objects) == 0: # No objects found in that file
        # Objects defined via cfg_file= should not be removed because nagios will not reload
        # after you remove the file
        for k,v, in pynag.Model.config.maincfg_values:
            if k == 'cfg-file' and v == i:
                continue
        print("Empty config file: %s" % i)
        # os.remove(i)
