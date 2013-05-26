import unittest
from mock import MagicMock, patch

import os
import shutil
import tempfile
import pynag.Utils as utils
import pynag.Model
from pynag.Utils import PynagError
from tests.test import tests_dir

class testUtils(unittest.TestCase):
    def setUp(self):
        # Utils should work fine with just about any data, but lets use testdata01
        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.config = None
        pynag.Model.cfg_file = './nagios/nagios.cfg'
        s = pynag.Model.ObjectDefinition.objects.all
        self.tmp_dir = tempfile.mkdtemp() # Will be deleted after test runs

    def tearDown(self):
        shutil.rmtree(self.tmp_dir,ignore_errors=True)

    def testCompareFilterWithGrep(self):
        """ test pynag.Utils.grep() by comparing it with pynag.Model.Service.objects.filter()

        # TODO: Currently  pynag.Model.Service.objects.filter() has some bugs, so some tests here fail.
        """
        result = self._compare_search_expressions(use='generic-service')

        result = self._compare_search_expressions(register=1,use='generic-service')

        result = self._compare_search_expressions(host_name__exists=True)

        result = self._compare_search_expressions(host_name__exists=False)

        result = self._compare_search_expressions(host_name__notcontains='l')

        result = self._compare_search_expressions(host_name__notcontains='this value cannot possibly exist')

        result = self._compare_search_expressions(host_name__startswith='l')

        result = self._compare_search_expressions(host_name__endswith='m')

        result = self._compare_search_expressions(host_name__isnot='examplehost for testing purposes')

    def testGrep(self):
        """ Test cases based on gradecke's testing """
        host = pynag.Model.string_to_class['host']()
        host['use'] = "generic-host"
        host['name'] = "ABC"
        host['_code'] = "ABC"
        host['_function'] = "Server,Production"

        host2 = pynag.Model.string_to_class['host']()
        host2['use'] = "generic-host"
        host2['name'] = "XYZ"
        host2['_code'] = "XYZ"
        host2['_function'] = "Switch,Production"

        hosts = host, host2

        result = pynag.Utils.grep(hosts, **{'_code__contains': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__contains': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'AB'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': True})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': False})
        self.assertEqual(0, len(result))

        result = pynag.Utils.grep(hosts, **{'_function__has_field': 'Server'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_function__has_field': 'Production'})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'name__notcontains': 'A'})
        self.assertEqual(1, len(result))


    def _compare_search_expressions(self, **expression):
        #print "Testing search expression %s" % expression
        all_services = pynag.Model.Service.objects.all
        result1 = pynag.Model.Service.objects.filter(**expression)
        result2 = pynag.Utils.grep(all_services, **expression)
        self.assertEqual(result1, result2,msg="Search output from pynag.Utils.grep() does not match pynag.Model.Service.objects.filter() when using parameters %s\nFilter: %s\nGrep: %s" % (expression, result1, result2))
        return len(result1)


    def test_run_command_file_not_found(self):
        command = '/bin/doesnotexist'
        expected_msg = '\* Could not run command \(return code= %s\)\n' % 127
        expected_msg += '\* Error was:\n.*: %s: (not found|No such file or directory)\n' % command
        expected_msg += '\* Command was:\n%s\n' % command
        expected_msg += '\* Output was:\n\n'
        expected_msg += 'Check if y/our path is correct: %s' % os.getenv('PATH')
        # TODO change to unittest2 so assertRaisesRegexp works for python 2.6
        """
        with self.assertRaisesRegexp(utils.PynagError, expected_msg):
            utils.runCommand(command, raise_error_on_fail=True)
        """
        import re
        try:
            utils.runCommand(command, raise_error_on_fail=True)
        except PynagError, message:
            match = re.match(expected_msg, message.args[0])
            self.assertNotEqual(match, None)
        else:
            self.fail("PynagError not raised.")

    def test_gitrepo_init_empty(self):
        from getpass import getuser
        from platform import node
        repo = utils.GitRepo(
                directory = self.tmp_dir, 
                auto_init = True,
                author_name = None,
                author_email = None
            )
        self.assertEquals(repo.author_name, 'Pynag User')
        expected_email = '<%s@%s>' % (getuser(), node())
        self.assertEquals(repo.author_email, expected_email)

    def test_gitrepo_init_with_files(self):
        tmp_file = tempfile.mkstemp(dir=self.tmp_dir)
        # If pynag defaults will fail, correctly, adjust for test
        author_email = None
        from getpass import getuser
        from platform import node
        nodename = node()
        if nodename.endswith('.(none)'):
            nodename[:-7]+'.example.com'
            author_email = '%s@%s' % (getuser(), nodename)
        repo = utils.GitRepo(
                directory = self.tmp_dir,
                auto_init = True,
                author_name = None,
                author_email = author_email
            )
        # Check that there is an initial commit
        expected_email = '%s@%s' % (getuser(), nodename)
        self.assertEquals(len(repo.log()), 1)
        self.assertEquals(repo.log()[0]['comment'], 'Initial Commit')
        self.assertEquals(repo.log()[0]['author_name'], 'Pynag User')
        self.assertEquals(repo.log()[0]['author_email'], expected_email)
        # Test kwargs functionality
        self.assertEquals(repo.log(author_email=expected_email)[0]['author_email'], expected_email)
        self.assertEquals(repo.log(comment__contains='Initial')[0]['comment'], 'Initial Commit')
        self.assertEquals(len(repo.log(comment__contains='nothing')), 0)
        # Test show method
        initial_hash = repo.log()[0]['hash']
        initial_hash_valid_commits = repo.get_valid_commits()[0]
        self.assertEquals(initial_hash, initial_hash_valid_commits)
        with patch('pynag.Utils.GitRepo._run_command') as gitrunpatch:
            with patch('pynag.Utils.GitRepo.get_valid_commits') as validcommitspatch:
                validcommitspatch.return_value = [initial_hash]
                repo.show(initial_hash)
                gitrunpatch.assert_called_once_with('git show %s' % initial_hash)
        invalid_hash = '123'
        # TODO assertRaises, repo.show(invalid_hash) PynagError('123 not a valid commit id')
        # Add file
        tmp_file_2 = tempfile.mkstemp(dir=self.tmp_dir)
        self.assertEquals(len(repo.get_uncommited_files()), 1)
        self.assertEquals(repo.is_up_to_date(), False)
        # Commit file
        repo.commit(filelist=repo.get_uncommited_files()[0]['filename'])
        self.assertEquals(repo.is_up_to_date(), True)
        self.assertEquals(len(repo.get_uncommited_files()), 0)
        self.assertEquals(len(repo.get_valid_commits()), 2)
        log_entry = repo.log()[0]
        self.assertEquals(log_entry['comment'], 'commited by pynag')
