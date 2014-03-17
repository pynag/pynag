#!/usr/bin/env python
import unittest
import doctest
import pynag.Model
import pynag.Parsers
import pynag.Plugins
import pynag.Control
import pynag.Utils


def load_tests(loader, tests, pattern):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest.TestSuite()

    # Add all doctests to our suite
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Plugins))
    suite.addTest(doctest.DocTestSuite(pynag.Parsers))
    suite.addTest(doctest.DocTestSuite(pynag.Control))
    suite.addTest(doctest.DocTestSuite(pynag.Model))
    suite.addTest(doctest.DocTestSuite(pynag.Utils))

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            suite.addTests(test_suite)
    return suite


if __name__ == '__main__':
    unittest.main()
