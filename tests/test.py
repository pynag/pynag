#!/usr/bin/env python
import os
import sys
import unittest2
import doctest

# Make sure all tests run from a fixed path, this also makes sure
# That pynag in local directory is imported before any system-wide
# installs of pynag
tests_dir = os.path.dirname(os.path.realpath(__file__)) or '.'
os.chdir(tests_dir)
sys.path.insert(0, os.path.realpath("%s/%s" % (tests_dir, os.path.pardir)))

import pynag.Model
import pynag.Parsers
import pynag.Plugins
import pynag.Control
import pynag.Utils


def load_tests(loader=None, tests=None, pattern=None):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest2.TestSuite()

    # Add all doctests to our suite
    suite.addTest(doctest.DocTestSuite(pynag.Model, setUp=setUpDocTests))
    suite.addTest(doctest.DocTestSuite(pynag.Parsers, setUp=setUpDocTests))
    suite.addTest(doctest.DocTestSuite(pynag.Plugins))
    suite.addTest(doctest.DocTestSuite(pynag.Control))
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Utils))

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest2.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            suite.addTests(test_suite)
    return suite


def setUpDocTests(doctest):
    """ For doctests that require a valid config to function, we point them
        to dataset01
    """
    os.chdir(os.path.join(tests_dir, 'dataset01'))
    pynag.Model.config = pynag.Parsers.config(cfg_file="./nagios/nagios.cfg")

if __name__ == '__main__':
    unittest2.main()