#!/usr/bin/env python
import os
import unittest2 as unittest
import doctest
import sys

tests_dir = os.path.dirname(os.path.realpath(__file__)) or '.'
os.chdir(tests_dir)
sys.path.insert(0, os.path.realpath("%s/%s" % (tests_dir, os.path.pardir)))


import pynag.Model
import pynag.Parsers
import pynag.Plugins
import pynag.Control
import pynag.Utils


import test_control
import test_command
import test_defaultdict
import test_model
import test_other
import test_parsers
import test_plugins
import test_utils


def load_tests(loader=None, tests=None, pattern=None):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest.TestSuite()

    # Add all doctests to our suite
    suite.addTest(doctest.DocTestSuite(pynag.Model, setUp=setUpDocTests))
    suite.addTest(doctest.DocTestSuite(pynag.Plugins))
    suite.addTest(doctest.DocTestSuite(pynag.Parsers, setUp=setUpDocTests))
    suite.addTest(doctest.DocTestSuite(pynag.Control))
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Utils))

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            suite.addTests(test_suite)
    return suite


def setUpDocTests(doctest):
    # The parser needs a Nagios config environment
    # we'll use dataset01 in the tests directory
    os.chdir(os.path.join(tests_dir, 'dataset01'))
    pynag.Model.config = pynag.Parsers.config(cfg_file="./nagios/nagios.cfg")

if __name__ == '__main__':
    state = unittest.TextTestRunner().run(load_tests())
    if state.failures or state.errors:
        sys.exit(1)
    sys.exit(0)
