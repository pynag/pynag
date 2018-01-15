#!/usr/bin/env python
#
# This pynag script will parse all your nagios configuration
# And write a copy of every single object to /tmp/nagios/conf.d
#
# This can be very handy if your configuration files are a mess
# or if you are thinking about splitting a big file of services
# into one file per host
#
# The script will only write the copy to /tmp so you will
# have to manually remove old objects before you copy this
# into your /etc/nagios/conf.d or wherever you want to keep
# your objects



from __future__ import absolute_import
from __future__ import print_function
import pynag.Model
from pynag.Model import ObjectDefinition
import os
import os.path

# cfg_file is where our main nagios config file is
pynag.Model.cfg_file = '/etc/nagios3/nagios.cfg'

# pynag_directory is where the new objects will be saved
pynag.Model.pynag_directory = '/tmp/nagios/conf.d'

all_objects = ObjectDefinition.objects.all
# Use this instead if you only want to clean up a single directory
# all_objects = ObjectDefinition.objects.filter(filename__contains='/etc/nagios/all_the_services.cfg')

for i in all_objects:
    print("Saving", i.object_type, i.get_description(), "...", end=' ')
    # Set a new filename for our object, None means
    # That pynag decides where it goes
    new_filename = i.get_suggested_filename()
    print(new_filename)
    continue
    # Alternative:
    # if i.object.type == 'host' and i.host_name is not None:
    #     new_filename = '/tmp/nagios/conf.d/hosts/%s" % i.host_name
    
    dirname = os.path.dirname(new_filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(new_filename, 'a') as f:
        data = "\n" + str(i)
        f.write(data)
    print(new_filename)

