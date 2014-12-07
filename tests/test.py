#!/usr/bin/env python
import os
import sys
import fnmatch

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2
import doctest
import mock

# Make sure all tests run from a fixed path, this also makes sure
# That pynag in local directory is imported before any system-wide
# installs of pynag
from tests import tests_dir

import pynag.Model
import pynag.Parsers
import pynag.Plugins
import pynag.Control
import pynag.Utils


def get_python_files():
    """Get a list of all python files inside pynag subdirectory"""
    matches = []
    for root, dirnames, filenames in os.walk(pynagbase + '/pynag/'):
        for filename in fnmatch.filter(filenames, '*.py'):
            matches.append(os.path.join(root, filename))
    return matches


def load_tests(loader=None, tests=None, pattern=None):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest2.TestSuite()

    # Add all doctests to our suite
    for filename in get_python_files():
        print "Looking for doctests in", filename
        doctest.DocFileSuite(filename, module_relative=False, setUp=set_up_for_doc_tests)

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest2.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            suite.addTests(test_suite)

    return suite


def set_up_for_doc_tests(test_case):
    """For doctests that require a valid config to function, we point them to dataset01."""
    os.chdir(os.path.join(tests_dir, 'dataset01'))
    pynag.Model.config = pynag.Parsers.config(cfg_file="./nagios/nagios.cfg")

if __name__ == "__main__":
    unittest2.main()

# vim: sts=4 expandtab autoindent
