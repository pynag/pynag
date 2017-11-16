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

class BuildMan(Command):
    """Builds the man page using sphinx"""
    user_options = []


    def run(self):
        cmd = "sphinx-build -b man docs man"
        sphinx_proc = Popen(cmd.split(),
                            stdout=PIPE,
                            stderr=PIPE)
        stdout, stderr = sphinx_proc.communicate()
        return_code = sphinx_proc.wait()
        if return_code:
            print("Warning: Build of manpage failed \"%s\":\n%s\n%s" % (
                      cmd,
                      stdout,
                      stderr))
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


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

def check_python_version():
    """Check if the python version is outdated"""
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        raise SystemExit("python 2.6 or newer is required")

if __name__ == "__main__":
    check_python_version()
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
        data_files=[(manpath, ['man/pynag.1.gz',]),],
        cmdclass={
            'test': PynagTest,
            'build_man': BuildMan,
        },
        requires=['unittest2'],
    )
