#!/usr/bin/env python
import os
import unittest
import doctest
import pynag.Model
import pynag.Parsers
import pynag.Plugins
import pynag.Control
import pynag.Utils

tests_dir = os.path.dirname(os.path.realpath(__file__)) or '.'
os.chdir(tests_dir)

import tests.test_control
import tests.test_command
import tests.test_defaultdict
import tests.test_model
import tests.test_other
import tests.test_parsers
import tests.test_plugins
import tests.test_utils


def load_tests(loader, tests, pattern):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest.TestSuite()

    # Add all doctests to our suite
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Plugins))
    suite.addTest(doctest.DocTestSuite(pynag.Parsers, setUp=setUpParserDoctest))
    suite.addTest(doctest.DocTestSuite(pynag.Control))
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Utils))

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            suite.addTests(test_suite)
    return suite

def setUpParserDoctest(doctest):
    # The parser needs a Nagios config environment
    # we'll use dataset01 in the tests directory
    os.chdir(os.path.join(tests_dir, 'dataset01'))

if __name__ == '__main__':
    unittest.main()
