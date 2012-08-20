#!/usr/bin/python

# This script parses the configmain.html file from the Nagios project and tries
# to extract information regarding options.

import re
from pprint import pprint

f = open('configmain.html')

k = None
p = False
doc = ""
format = ""
examples = []
options = []
title = ""
info = {}

for l in f.readlines():
    # no newline
    l = l[:-1]

    # Empty line
    if not len(l):
        continue

    # no config key and we are not at the start of a config key section
    if k is None and l.startswith('<a name=') is False:
        continue
    # Find the start of a key section
    m = re.match(r'<a name="(?P<key>.+?)"', l)
    if m:
        # New config key, storing the last one
        if k:
            info[k] = {
                'title': title,
                'doc': doc,
                'format': format,
                'examples': examples,
                'options': options
            }

            # Reset variables
            k = None
            p = False
            options = []
            doc = ""
            format = ""
            title = ""
            examples = []
        # We are not on this config key
        k = m.group('key')
        continue

    # Get the Format string
    m = re.match(r'.*<td><strong>(?P<format>.+?)</strong>', l)
    if m:
        format = m.group('format')
        continue

    # This config key has examples
    m = re.match(r'.*<font color="red"><strong>(?P<example>.+?)</strong>', l)
    if m:
        examples.append(m.group('example'))
        continue

    # More descriptive title for the config key
    m = re.match(r'.*<td bgcolor="#cbcbcb"><strong>(?P<title>.+?)</strong>', l)
    if m:
        title = m.group('title')
        continue

    # Here starts the main doc string
    if l == "<p>":
        p = True
        continue

    # Here ends the doc string
    if l == "</p>":
        p = False
        continue

    # Description of the options
    if l[:4] == '<li>':
        options.append(l[4:])

    # We are in the main doc section
    if p and k:
        doc += "%s " % (l)

# Save the last config key
info[k] = {
    'title': title,
    'doc': doc,
    'format': format,
    'examples': examples,
    'options': options
}

# PrettyPrint
pprint(info)
# vim: smartindent tabstop=4 shiftwidth=4 expandtab
