#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" General Utilities from importing nagios objects. Currently .csv files are supported

Either execute this script standalone from the command line or use it as a python library like so:

>>> from pynag.Utils import importer
>>> pynag_objects = importer.import_from_csv_file(filename='foo', seperator=',') # doctest: +SKIP
>>> for i in pynag_objects: # doctest: +SKIP
...     i.save() # doctest: +SKIP
"""

import optparse
import os

import pynag.Model

# Default host is used when you try to add a service to a
# Host that does not exist
DEFAULT_HOST_ATTRIBUTES = {
    'use': 'generic-host',
    'check_command': 'check-host-alive',
    'check_interval': '1',
    'max_check_attempts': '3',
    'retry_interval': '2',
}


options = optparse.OptionParser()
options.add_option(
    '--destination_filename',
    dest='destination_filename',
    default=None,
    help='Destination file where objects will be saved',
)
options.add_option(
    '--seperator',
    dest='seperator',
    default=',',
    help='Use this as seperator for columns (default: ,)',
)
options.add_option(
    '--dry_run',
    dest='dry_run',
    default=False,
    action='store_true',
    help='If specified, only print object definitions to screen',
)
options.add_option(
    '--object_type',
    dest='object_type',
    default=None,
    help='Assume this object type (e.g. "host") if its not specified in file'
)


def parse_arguments():
    """ Parse command line arguments """
    (opts, args) = options.parse_args()
    return opts, args


def main():
    (opts, args) = parse_arguments()

    if not args:
        options.error("You must specify at least one .csv file as an argument")
    for i in args:
        if not os.path.isfile(i):
            options.error("Could not find file: %s" % i)
    pynag_objects = []
    for i in args:
        tmp = import_from_csv_file(filename=i, seperator=opts.seperator, object_type=opts.object_type)
        pynag_objects += tmp

    if opts.dry_run:
        print(len(pynag_objects))
        for i in pynag_objects:
            print(i)
    else:
        for i in pynag_objects:
            i.save(filename=opts.destination_filename)


def dict_to_pynag_objects(dict_list, object_type=None):
    """Take a list of dictionaries, return a list of pynag.Model objects.

    Args:
        dict_list: List of dictionaries that represent pynag objects
        object_type: Use this object type as default, if it is not specified in dict_list
    Returns:
        List of pynag objects
    """
    result = []
    for i in dict_list:
        dictionary = i.copy()
        object_type = dictionary.pop("object_type", object_type)
        if not object_type:
            raise ValueError('One column needs to specify object type')
        Class = pynag.Model.string_to_class[object_type]
        pynag_object = Class(**dictionary)
        result.append(pynag_object)
    return result


def parse_csv_file(filename, seperator=','):
    """ Parse filename and return a dict representing its contents """
    with open(filename) as f:
        data = f.read()
        return parse_csv_string(data, seperator=seperator)


def parse_csv_string(csv_string, seperator=','):
    """ Parse csv string and return a dict representing its contents """
    result = []
    lines = csv_string.splitlines()
    headers = None
    for line in lines:
        # Skip empty lines
        if not line:
            continue
        # If this is first line
        if not headers:
            headers = [x.strip() for x in line.split(seperator)]
            continue
        mydict = {}
        result.append(mydict)
        columns = [x.strip() for x in line.split(seperator)]
        for i, column in enumerate(columns):
            header = headers[i]
            mydict[header] = column
    return result


def import_from_csv_file(filename, seperator=',', object_type=None):
    """ Parses filename and returns a list of pynag objects.

    Args:
        filename: Path to a file
        seperator: use this symbol to seperate columns in the file
        object_type: Assume this object_type if there is no object_type column
    """
    dicts = parse_csv_file(filename=filename, seperator=seperator)
    pynag_objects = dict_to_pynag_objects(dicts, object_type=object_type)
    return pynag_objects

if __name__ == '__main__':
    main()
