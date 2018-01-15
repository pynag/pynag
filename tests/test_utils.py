from __future__ import absolute_import
import os
import sys

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2 as unittest
from mock import patch
import shutil
import tempfile
import pynag.Utils as utils
import pynag.Model
from pynag.Utils import PynagError
from tests import tests_dir
import pynag.Utils.misc


class testUtils(unittest.TestCase):

    def setUp(self):
        # Utils should work fine with just about any data, but lets use
        # testdata01
        os.chdir(tests_dir)
        os.chdir('dataset01')
        pynag.Model.config = None
        pynag.Model.cfg_file = './nagios/nagios.cfg'
        pynag.Model.ObjectDefinition.objects.get_all()
        self.tmp_dir = tempfile.mkdtemp()  # Will be deleted after test runs
        os.environ['LANG'] = 'en_US@UTF8'

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def testCompareFilterWithGrep(self):
        """ test pynag.Utils.grep() by comparing it with pynag.Model.Service.objects.filter()

        # TODO: Currently  pynag.Model.Service.objects.filter() has some bugs, so some tests here fail.
        """
        self._compare_search_expressions(use='generic-service')

        self._compare_search_expressions(register=1, use='generic-service')

        self._compare_search_expressions(host_name__exists=True)

        self._compare_search_expressions(host_name__exists=False)

        self._compare_search_expressions(host_name__notcontains='l')

        self._compare_search_expressions(host_name__notcontains='this value cannot possibly exist')

        self._compare_search_expressions(host_name__startswith='l')

        self._compare_search_expressions(host_name__endswith='m')

        self._compare_search_expressions(host_name__isnot='examplehost for testing purposes')

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

        # Check that contains does not match nonexisting values
        result = pynag.Utils.grep(hosts, **{'_code__contains': ''})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'nonexistant__contains': ''})
        self.assertEqual(0, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notcontains': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__startswith': 'AB'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notstartswith': 'AB'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'ABC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__endswith': 'BC'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__notendswith': 'YZ'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': True})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'_code__exists': False})
        self.assertEqual(0, len(result))

        result = pynag.Utils.grep(hosts, **{'_function__has_field': 'Server'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(
            hosts, **{'_function__has_field': 'Production'})
        self.assertEqual(2, len(result))

        result = pynag.Utils.grep(hosts, **{'name__notcontains': 'A'})
        self.assertEqual(1, len(result))

        result = pynag.Utils.grep(hosts, **{'name__regex': 'A.C'})
        self.assertEqual(1, len(result))
        self.assertEqual('ABC', result[0].name)

        result = pynag.Utils.grep(hosts, **{'name__in': ['ABC', 'BCD']})
        self.assertEqual(1, len(result))
        self.assertEqual('ABC', result[0].name)

        result = pynag.Utils.grep(hosts, **{'name__notin': ['ABC', 'BCD']})
        self.assertEqual(1, len(result))
        self.assertEqual('XYZ', result[0].name)

        result = pynag.Utils.grep(hosts, **{'search': 'Switch'})
        self.assertEqual(1, len(result))
        self.assertEqual('XYZ', result[0].name)

    def _compare_search_expressions(self, **expression):
        # print "Testing search expression %s" % expression
        all_services = pynag.Model.Service.objects.all
        result1 = pynag.Model.Service.objects.filter(**expression)
        result2 = pynag.Utils.grep(all_services, **expression)
        self.assertEqual(
            result1, result2, msg="Search output from pynag.Utils.grep() does not match pynag.Model.Service.objects.filter() when using parameters %s\nFilter: %s\nGrep: %s" %
            (expression, result1, result2))
        return len(result1)

    def test_run_command_file_not_found(self):
        command = '/bin/doesnotexist'
        expected_msg = '\* Could not run command \(return code= %s\)\n' % 127
        expected_msg += '\* Error was:\n.*: %s: (not found|No such file or directory)\n' % command
        expected_msg += '\* Command was:\n%s\n' % command
        expected_msg += '\* Output was:\n\n'
        expected_msg += 'Check if y/our path is correct: %s' % os.getenv(
            'PATH')
        self.assertRaisesRegexp(
            utils.PynagError, expected_msg, utils.runCommand, command, raise_error_on_fail=True)

    def test_gitrepo_init_empty(self):
        from getpass import getuser
        from platform import node
        emptyish = [None, '', ' ', '\n    ']
        for x in emptyish:
            repo = utils.GitRepo(
                directory=self.tmp_dir,
                auto_init=True,
                author_name=x,
                author_email=x
            )
            self.assertEquals(repo.author_name, 'Pynag User')
            expected_email = '%s@%s' % (getuser(), node())
            self.assertEquals(repo.author_email, expected_email)

    def test_gitrepo_init_with_author(self):
        tempfile.mkstemp(dir=self.tmp_dir)
        author_name = 'Git Owner'
        author_email = 'git@localhost.local'
        repo = utils.GitRepo(
            directory=self.tmp_dir,
            auto_init=True,
            author_name=author_name,
            author_email=author_email
        )
        self.assertEquals(repo.author_name, author_name)
        self.assertEquals(repo.author_email, author_email)
        self.assertEquals(len(repo.log()), 1)
        self.assertEquals(repo.log()[0]['author_name'], author_name)
        self.assertEquals(repo.log()[0]['author_email'], author_email)

    def test_gitrepo_init_with_files(self):
        tempfile.mkstemp(dir=self.tmp_dir)
        # If pynag defaults will fail, correctly, adjust for test
        author_email = None
        from getpass import getuser
        from platform import node
        nodename = node()
        if nodename.endswith('.(none)'):
            nodename[:-7] + '.example.com'
            author_email = '%s@%s' % (getuser(), nodename)
        repo = utils.GitRepo(
            directory=self.tmp_dir,
            auto_init=True,
            author_name=None,
            author_email=author_email
        )
        # Check that there is an initial commit
        expected_email = '%s@%s' % (getuser(), nodename)
        self.assertEquals(len(repo.log()), 1)
        self.assertEquals(repo.log()[0]['comment'], 'Initial Commit')
        self.assertEquals(repo.log()[0]['author_name'], 'Pynag User')
        self.assertEquals(repo.log()[0]['author_email'], expected_email)
        # Test kwargs functionality
        self.assertEquals(
            repo.log(author_email=expected_email)[0]['author_email'], expected_email)
        self.assertEquals(
            repo.log(comment__contains='Initial')[0]['comment'], 'Initial Commit')
        self.assertEquals(len(repo.log(comment__contains='nothing')), 0)
        # Test show method
        initial_hash = repo.log()[0]['hash']
        initial_hash_valid_commits = repo.get_valid_commits()[0]
        self.assertEquals(initial_hash, initial_hash_valid_commits)

        gitrunpatcher = patch('pynag.Utils.GitRepo._run_command')
        validcommitspatcher = patch('pynag.Utils.GitRepo.get_valid_commits')
        gitrunpatch = gitrunpatcher.start()
        validcommitspatch = validcommitspatcher.start()
        validcommitspatch.return_value = [initial_hash]
        repo.show(initial_hash)
        gitrunpatch.assert_called_once_with('git show %s' % initial_hash)
        gitrunpatcher.stop()
        validcommitspatcher.stop()

        self.assertRaisesRegexp(
            PynagError, '%s is not a valid commit id' % initial_hash)
        # Add file
        tempfile.mkstemp(dir=self.tmp_dir)
        self.assertEquals(len(repo.get_uncommited_files()), 1)
        self.assertEquals(repo.is_up_to_date(), False)
        # Commit file
        repo.commit(filelist=repo.get_uncommited_files()[0]['filename'])
        self.assertEquals(repo.is_up_to_date(), True)
        self.assertEquals(len(repo.get_uncommited_files()), 0)
        self.assertEquals(len(repo.get_valid_commits()), 2)
        log_entry = repo.log()[0]
        self.assertEquals(log_entry['comment'], 'commited by pynag')

    def test_gitrepo_deprecated_methods(self):
        """
        Delete this class as deprecated methods are removed.
        """
        repo = utils.GitRepo(directory=self.tmp_dir, auto_init=True)
        testfilename = 'testfile.name.txt'

        add_method_patcher = patch('pynag.Utils.GitRepo.add')
        add_method_patch = add_method_patcher.start()
        repo._git_add(testfilename)
        add_method_patch.assert_called_once_with(testfilename)
        add_method_patcher.stop()

        commit_method_mocker = patch('pynag.Utils.GitRepo.commit')
        commit_method_mock = commit_method_mocker.start()
        repo._git_commit(filename=testfilename, message='test')
        commit_method_mock.assert_called_once_with(
            message='test', filelist=[testfilename])
        commit_method_mock.reset_mock()
        repo._git_commit(
            filename=None, message='test', filelist=[testfilename])
        commit_method_mock.assert_called_once_with(
            message='test', filelist=[testfilename])
        commit_method_mock.reset_mock()
        repo._git_commit(
            filename=testfilename, message='test', filelist=[testfilename])
        commit_method_mock.assert_called_once_with(
            message='test', filelist=[testfilename, testfilename])
        commit_method_mocker.stop()

    def test_gitrepo_diff(self):
        """ Test git diff works as expected  """
        # Create repo and write one test commit
        git = utils.GitRepo(directory=self.tmp_dir, auto_init=True)
        tmp_filename = "%s/%s" % (self.tmp_dir, 'testfile.txt')
        open(tmp_filename, 'w').write('test data\n')
        git.commit()

        # First try diff with no changes made:
        diff = git.diff()
        self.assertEquals(diff, '')

        # Now append to our file and see the difference:
        extra_data = 'extra data\n'
        open(tmp_filename, 'a').write(extra_data)

        # Call diff with no params, check if extra_data is in the diff
        diff = git.diff()

        self.assertTrue(diff.find(extra_data) > 0)

        # Call diff with filename as parameter, check if extra_data is in the
        # diff
        diff = git.diff(commit_id_or_filename=tmp_filename)
        self.assertTrue(diff.find(extra_data) > 0)

        # Call commit again and confirm there is no diff
        git.commit()
        diff = git.diff()
        self.assertEquals(diff, '')

        # Call a diff against first commit, see if we find our changes in the
        # commit.
        all_commits = git.get_valid_commits()
        first_commit = all_commits.pop()
        diff = git.diff(commit_id_or_filename=first_commit)
        self.assertTrue(diff.find(extra_data) > 0)

        # Revert latest change, and make sure diff is gone.
        last_commit = all_commits.pop(0)
        git.revert(last_commit)
        diff = git.diff(commit_id_or_filename=first_commit)
        self.assertTrue(diff.find(extra_data) == -1)

        # At last try to diff against an invalid commit id
        try:
            git.diff('invalid commit id')
            self.assertTrue(
                False, "we wanted exception when calling diff on invalid commit id")
        except PynagError:
            pass

    def test_send_nsca(self):
        """ test pynag.Utils.send_nsca

        By its very nature, send_nsca binary itself does not allow for much testing,
        however we can still test if the function is working as expected
        """

        # Run send_nsca normally for a smoke test (we don't know much about what send_nsca will do with out packet)
        # This test will only fail if there are unhandled tracebacks in the
        # code somewhere
        try:
            pynag.Utils.send_nsca(code=0, message="test", nscahost="localhost")
        except OSError as e:
            # We don't care about the result if we have error because send_nsca
            # is not installed
            if e.errno != 2:
                raise e

        result = pynag.Utils.send_nsca(
            code=0, message="match", nscahost="match", hostname="test", service=None, nscabin="/bin/grep", nscaconf="-")
        self.assertEqual(0, result[0])
        self.assertEqual('(standard input):1\n', result[1])

        result = pynag.Utils.send_nsca(
            code=0, message="match", nscahost="nomatch", hostname="test", service=None, nscabin="/bin/grep", nscaconf="-")
        self.assertEqual(1, result[0])
        self.assertEqual('(standard input):0\n', result[1])


class testFakeNagiosEnvironment(unittest.TestCase):

    def setUp(self):
        self.environment = pynag.Utils.misc.FakeNagiosEnvironment()
        self.environment.create_minimal_environment()

    def tearDown(self):
        self.environment.terminate()

    def testMinimal(self):
        """ Minimal Test of our FakeNagiosEnvironment """
        nagios = pynag.Utils.misc.FakeNagiosEnvironment()
        nagios.create_minimal_environment()
        nagios.config.parse()
        self.assertTrue(os.path.isfile(nagios.config.cfg_file))
        self.assertTrue(os.path.isdir(nagios.objects_dir))

    def testModelUpdates(self):
        """ Test backup and restores of Model global variables """
        nagios = self.environment
        original_config = pynag.Model.config
        original_cfg_file = pynag.Model.cfg_file
        original_dir = pynag.Model.pynag_directory

        # Update model, and check if updates succeeded
        nagios.update_model()
        self.assertEqual(pynag.Model.config, nagios.config)
        self.assertEqual(pynag.Model.cfg_file, nagios.config.cfg_file)
        self.assertEqual(pynag.Model.pynag_directory, nagios.objects_dir)

        # See if we can restore our model
        nagios.restore_model()
        self.assertEqual(pynag.Model.config, original_config)
        self.assertEqual(pynag.Model.cfg_file, original_cfg_file)
        self.assertEqual(pynag.Model.pynag_directory, original_dir)

    def testStartStop(self):
        """ Try to start and stop our nagios environment  """
        self.environment.start()
        pid = open(os.path.join(self.environment.tempdir, "nagios.pid")).read()
        pid = int(pid)
        try:
            os.kill(pid, 0)
        except OSError:
            self.assertTrue(False, "Did not find a running process with process_id=%s" % pid)
        self.environment.stop()
        try:
            os.kill(pid, 0)
            self.assertTrue(False, "Seems like process with process_id=%s is still running" % pid)
        except OSError:
            pass

    def testOpenDecorator(self):
        """ Makes sure the fake nagios environment cannot go outside its directory """
        # Try to open a regular file
        self.environment.config.open(self.environment.config.cfg_file).close()
        self.assertTrue(True, "Successfully opened nagios.cfg")
        try:
            self.environment.config.open("/etc/passwd").close()
            self.assertTrue(False, "I was able to open a file outside my tempdir!")
        except PynagError:
            pass

    def testUpdateModel_NoRestore(self):
        self.environment.update_model()

    def testLivestatus(self):
        host_name = "localhost"
        self.environment.update_model()
        pynag.Model.Host(host_name=host_name, use="generic-host").save()

        self.environment.guess_livestatus_path()
        self.environment.configure_livestatus()
        self.environment.start()
        livestatus = self.environment.get_livestatus()
        hosts = livestatus.get_hosts(name=host_name)
        self.assertTrue(hosts, "Could not find a host called %s" % (host_name))

    def testImports(self):
        """ Test FakeNagiosEnvironment.import_config()  """
        host1 = "host1"
        host2 = "host2"
        tempdir = tempfile.mkdtemp()
        tempfile1 = tempfile.mktemp(suffix='.cfg')
        tempfile2 = os.path.join(tempdir, 'file2.cfg')

        with open(tempfile1, 'w') as f:
            f.write("define host {\nname host1\n}")
        with open(tempfile2, 'w') as f:
            f.write("define host {\nname host2\n}")

        self.environment.import_config(tempdir)
        self.environment.import_config(tempfile1)

        self.environment.update_model()
        host1 = pynag.Model.Host.objects.filter(name=host1)
        host2 = pynag.Model.Host.objects.filter(name=host2)
        self.assertTrue(host1)
        self.assertTrue(host2)

if __name__ == "__main__":
    unittest.main()

# vim: sts=4 expandtab autoindent
