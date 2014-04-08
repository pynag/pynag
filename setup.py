#!/usr/bin/python

## setup.py ###
from distutils.core import setup, Command
from distutils.command.build_py import build_py as _build_py
from pynag import __version__
from subprocess import call, PIPE, Popen
import sys

NAME = "pynag"
SHORT_DESC = "Python modules for Nagios plugins and configuration"
LONG_DESC = """
Python modules and utilities for pragmatically handling Nagios configuration
file maintenance, status information, log file parsing and plug-in development.
"""

def build_man():
    """Builds the man page using sphinx"""
    cmd = "sphinx-build -b man docs man"
    try:
        sphinx_proc = Popen(cmd.split(),
                            stdout=PIPE,
                            stderr=PIPE)
        stdout, stderr = sphinx_proc.communicate()
        return_code = sphinx_proc.wait()
        if return_code:
            print "Warning: Build of manpage failed \"%s\":\n%s\n%s" % (
                      cmd,
                      stdout,
                      stderr)
    except OSError, error:
        print "Warning: Build of manpage failed \"%s\" you probably dont " \
              "have sphinx installed: %s" % (cmd, error)


class build_py(_build_py):
    """Overwrite build_py to install man building into the chain"""
    def run(self):
        build_man()
        _build_py.run(self)


class PynagTest(Command):
    """Runs the build-test.py testing suite"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = call([sys.executable, 'tests/build-test.py'])
        raise SystemExit(errno)

if __name__ == "__main__":
    manpath = "share/man/man1"
    etcpath = "/etc/%s" % NAME
    etcmodpath = "/etc/%s/modules" % NAME
    initpath = "/etc/init.d/"
    logpath = "/var/log/%s/" % NAME
    varpath = "/var/lib/%s/" % NAME
    rotpath = "/etc/logrotate.d"
    setup(
        name='%s' % NAME,
        version=__version__,
        author='Drew Stinnett',
        description=SHORT_DESC,
        long_description=LONG_DESC,
        author_email='drew@drewlink.com',
        url='http://pynag.org/',
        license='GPLv2',
        scripts=['scripts/pynag'],
        packages=[
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
        data_files=[(manpath, ['man/pynag.1',]),],
        cmdclass={
            'test': PynagTest,
            'build_py': build_py,
        },
        requires=['unittest2'],
    )
