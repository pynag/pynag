#!/usr/bin/python

## setup.py ###
from distutils.core import setup, Command
from pynag import __version__

NAME = "pynag"
SHORT_DESC = "Python modules for Nagios plugins and configuration" 
LONG_DESC = """
Python modules and utilities for pragmatically handling Nagios configuration
file maintenance, status information, log file parsing and plug-in development.
"""

class PynagTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    #def parse_command
    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'tests/build-test.py'])
        raise SystemExit(errno)

if __name__ == "__main__":
    manpath        = "share/man/man1"
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
        url='http://pynag.org/',
        license='GPLv2',
        scripts = [
            'scripts/pynag'
        ],
        packages = [
            'pynag',
            'pynag.Model',
            'pynag.Model.EventHandlers',
            'pynag.Plugins',
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
        cmdclass = {'test': PynagTest}, requires=['unittest2'],
    )
