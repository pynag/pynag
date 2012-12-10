#!/usr/bin/python

## setup.py ###
from distutils.core import setup
from pynag import __version__

NAME = "pynag"
SHORT_DESC = "Python Modules for Nagios plugins and configuration" 
LONG_DESC = """
Contains python modules for pragmatically handling configuration
file maintenance and plugin development.
"""

if __name__ == "__main__":
    manpath        = "share/man/man1/"
    etcpath = "/etc/%s" % NAME
    etcmodpath    = "/etc/%s/modules" % NAME
    initpath    = "/etc/init.d/"
    logpath        = "/var/log/%s/" % NAME
    varpath        = "/var/lib/%s/" % NAME
    rotpath        = "/etc/logrotate.d"
    setup(
        name='%s' % NAME,
        version = __version__,
        author='Drew Stinnett',
        description = SHORT_DESC,
        long_description = LONG_DESC,
        author_email='drew@drewlink.com',
        url='http://code.google.com/p/pynag/',
        license='GPLv2',
        scripts = [
            'scripts/pynag'
        ],
        packages = [
            'pynag',
            'pynag.Model',
            'pynag.Model.EventHandlers',
            'pynag.Plugins',
            'pynag.Plugins.new_threshold_syntax',
            'pynag.Parsers',
            'pynag.Control',
            'pynag.Utils',
            'pynag.Control',
            'pynag.Control.Command',
        ],
          data_files = [(manpath, [
        'docs/pynag.1.gz',
        ]),
        ],
    )
