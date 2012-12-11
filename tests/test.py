# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2011 Pall Sigurdsson
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import unittest
import pynag.Model
import pynag.Parsers
import pynag.Utils
import pynag.Plugins
import doctest
import tempfile
import shutil
import os

class testSave(unittest.TestCase):
    """
    Basic Unit Tests that relate to saving objects
    """
    def setUp(self):
        """ Basic setup before test suite starts
        """
        self.tmp_dir = tempfile.mkdtemp() # Will be deleted after test runs
        #os.mkdir(self.tmp_dir)
        pynag.Model.pynag_directory = self.tmp_dir
    def tearDown(self):
        """ Clean up after test suite has finished
        """
        shutil.rmtree(self.tmp_dir,ignore_errors=True)
    def testSuggestedFileName(self):
        """ Test get_suggested_filename feature in pynag.Model
        """
        s1 = pynag.Model.Service()
        s1.service_description = 'Service without host_name'

        s2 = pynag.Model.Service()
        s2.service_description = 'Service with host_name'
        s2.host_name = 'host.example.com'

        s3 = pynag.Model.Service()
        s3.service_description = 'Service with Generic Name'
        s3.name = 'generic-test-service'

        s1_expected = '%s/services/Service without host_name.cfg' % pynag.Model.pynag_directory
        s2_expected = '%s/services/host.example.com/Service with host_name.cfg' % pynag.Model.pynag_directory
        s3_expected = '%s/services/generic-test-service.cfg' % pynag.Model.pynag_directory

        self.assertEqual(s1_expected, s1.get_suggested_filename() )
        self.assertEqual(s2_expected, s2.get_suggested_filename() )
        self.assertEqual(s3_expected, s3.get_suggested_filename() )

    def testParseDatasets(self):
        """ Parse every testdata*/nagios/nagios.cfg
        Output will be compared with testdata*/expectedoutput.txt
        """
        current_dir =  os.path.dirname(__file__)
        if current_dir == '':
            current_dir = '.'
        test_dirs = []
        for i in os.listdir(current_dir):
            if i.startswith('testdata') and os.path.isdir(i) and os.path.isfile(i + "/nagios/nagios.cfg"):
                test_dirs.append(i)

        for dir in test_dirs:
            os.chdir(dir)
            pynag.Model.cfg_file = "./nagios/nagios.cfg"
            pynag.Model.config = None
            actualOutput = ''
            expectedOutput = open("expected_output.txt").read()
            for i in pynag.Model.ObjectDefinition.objects.all:
                actualOutput += str(i)
            # Write our parsed data to tmpfile so we have an easy diff later:
            tmp_file = self.tmp_dir + "/" + os.path.basename(dir) + "_actual_output.txt"
            open(tmp_file,'w').write(actualOutput)
            diff_output = pynag.Utils.runCommand("diff -uwB expected_output.txt '%s'" % (tmp_file))[1]
            print diff_output
            self.assertEqual('', diff_output)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testSave))
    suite.addTests( doctest.DocTestSuite(pynag.Plugins) )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner().run( suite() )