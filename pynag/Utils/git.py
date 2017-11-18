""" Convenience class for handling git repos."""

from __future__ import absolute_import
import datetime
import subprocess
import os
import six
import sys
from getpass import getuser
from platform import node

from pynag.Utils import grep
from pynag.errors import PynagError
from six.moves import filter
from six.moves import map


class GitError(PynagError):
    """Base class for errors in this module."""


class GitRepo(object):

    def __init__(self, directory, auto_init=True, author_name="Pynag User", author_email=None):
        """ Python Wrapper around Git command line.

        Args:

            Directory (str): Path to the directory does the git repo reside in (i.e. '/etc/nagios')

            auto_init (bool): If True and directory does not contain a git repo, create it automatically

            author_name (str): Full name of the author making changes

            author_email (str): Email used for commit messages, if None, then use username@hostname
        """

        self.directory = directory

        # Who made the change
        if author_name is None or author_name.strip() == '':
            author_name = "Pynag User"
        if author_email is None or author_email.strip() == '':
            author_email = "%s@%s" % (getuser(), node())
        self.author_name = author_name
        self.author_email = author_email

        # Which program did the change
        #self.source = source

        # Every string in self.messages indicated a line in the eventual commit
        # message
        self.messages = []

        self.ignore_errors = False
        self._update_author()
        if auto_init:
            try:
                self._run_command('git status --short')
            except PynagError:
                t, e = sys.exc_info()[:2]
                if e.errorcode == 128:
                    self.init()
            #self._run_command('git status --short')

        self._is_dirty = self.is_dirty  # Backwards compatibility

    def _update_author(self):
        """ Updates environment variables GIT_AUTHOR_NAME and EMAIL

        Returns:
            None
        """
        os.environ['GIT_AUTHOR_NAME'] = self.author_name
        os.environ['GIT_AUTHOR_EMAIL'] = self.author_email

    def _run_command(self, command):
        """ Run a specified command from the command line. Return stdout

        Args:
            command (str): command to execute

        Returns:
            stdout of the executed command
        """
        cwd = self.directory
        proc = subprocess.Popen(command, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        stdout, stderr = proc.communicate('through stdin to stdout')
        returncode = proc.returncode
        if returncode > 0 and self.ignore_errors is False:
            errorstring = "Command '%s' returned exit status %s.\n stdout: %s \n stderr: %s\n Current user: %s"
            errorstring = errorstring % (command, returncode, stdout, stderr, getuser())
            raise GitError(errorstring, errorcode=returncode, errorstring=stderr)
        return stdout

    def is_up_to_date(self):
        """ Returns True if all files in git repo are fully commited

        Returns:
            bool. Git repo is up-to-date
                True -- All files are commited

                False -- At least one file is not commited
        """
        return len(self.get_uncommited_files()) == 0

    def get_valid_commits(self):
        """ Returns a list of all commit ids from git log

        Returns:
            List of all valid commit hashes
        """
        return [x.get('hash') for x in self.log()]

    def get_uncommited_files(self):
        """ Returns a list of files that are have unstaged changes

        Returns:
            List. All files that have unstaged changes.
        """
        output = self._run_command("git status --porcelain")
        result = []
        if not six.PY2 and isinstance(output, six.binary_type):
            output = output.decode()
        for line in output.split('\n'):
            line = line.split(None, 1)
            if len(line) < 2:
                continue
            status, filename = line[0], line[1]
            # If file has been renamed, git status shows output in the form of:
            # R nrpe.cfg -> nrpe.cfg~
            # We want only the last part of the filename
            if status == 'R':
                filename = filename.split('->')[1].strip()
            # If there are special characters in the name, git will double-quote the output
            # We will remove those quotes, but we cannot use strip because it will damage:
            # files like this: "\"filename with actual doublequotes\""
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]

            result.append({'status': status, 'filename': filename})
        return result

    def log(self, **kwargs):
        """ Returns a log of previous commits. Log is is a list of dict objects.

        Any arguments provided will be passed directly to pynag.Utils.grep() to filter the results.

        Args:
            kwargs: Arguments passed to pynag.Utils.grep()

        Returns:
            List of dicts. Log of previous commits.

        Examples:
          self.log(author_name='nagiosadmin')

          self.log(comment__contains='localhost')
        """
        raw_log = self._run_command("git log --pretty='%H\t%an\t%ae\t%at\t%s'")
        result = []
        for line in raw_log.splitlines():
            if not six.PY2 and isinstance(line, six.binary_type):
                line = line.decode()
            hash, author, authoremail, authortime, comment = line.split("\t", 4)
            result.append({
                "hash": hash,
                "author_name": author,
                "author_email": authoremail,
                "author_time": datetime.datetime.fromtimestamp(float(authortime)),
                "timestamp": float(authortime),
                "comment": comment,
            })
        return grep(result, **kwargs)

    def diff(self, commit_id_or_filename=None):
        """ Returns diff (as outputted by "git diff") for filename or commit id.

        If commit_id_or_filename is not specified. show diff against all uncommited files.

        Args:
            commit_id_or_filename (str): git commit id or file to diff with

        Returns:
            str. git diff for filename or commit id

        Raises:
            GitError: Invalid commit id or filename was given
        """
        if commit_id_or_filename in ('', None):
            command = "git diff"
        elif os.path.exists(commit_id_or_filename):
            commit_id_or_filename = commit_id_or_filename.replace("'", r"\'")
            command = "git diff '%s'" % commit_id_or_filename
        elif commit_id_or_filename in self.get_valid_commits():
            commit_id_or_filename = commit_id_or_filename.replace("'", r"\'")
            command = "git diff '%s'" % commit_id_or_filename
        else:
            raise GitError("%s is not a valid commit id or filename" % commit_id_or_filename)
        # Clean single quotes from parameters:
        return self._run_command(command)

    def show(self, commit_id,):
        """ Returns output from "git show" for a specified commit_id

        Args:
            commit_id (str): Commit id of the commit to display (``git show``)

        Returns:
            str. Output of ``git show commit_id``

        Raises:
            GitError: Invalid commit_id was given
        """
        if commit_id not in self.get_valid_commits():
            raise GitError("%s is not a valid commit id" % commit_id)
        command = "git show %s" % commit_id
        return self._run_command(command)

    def init(self):
        """ Initilizes a new git repo (i.e. run "git init") """
        self._update_author()
        self._run_command("git init")
        # Only do initial commit if there are files in the directory
        if not os.listdir(self.directory) == ['.git']:
            self.commit(message='Initial Commit')

    def _git_add(self, filename):
        """ Deprecated, use self.add() instead. """
        return self.add(filename)

    def _git_commit(self, filename, message, filelist=None):
        """ Deprecated. Use self.commit() instead."""
        if filelist is None:
            filelist = []
        if not filename is None:
            filelist.append(filename)
        return self.commit(message=message, filelist=filelist)

    def pre_save(self, object_definition, message):
        """ Commits object_definition.get_filename() if it has any changes.

        This function is called by :py:class:`pynag.Model.EventHandlers` before
        calling :py:meth:`pynag.Utils.GitRepo.save`

        Args:

            object_definition (pynag.Model.ObjectDefinition): object to commit changes

            message (str): git commit message as specified in  ``git commit -m``

        A message from the authors:
            *"Since this is still here, either i forgot to remove it, or because
            it is here for backwards compatibility, palli"*

        """
        filename = object_definition.get_filename()
        if self.is_dirty(filename):
            self._git_add(filename)
            self._git_commit(filename,
                             message="External changes commited in %s '%s'" %
                            (object_definition.object_type, object_definition.get_shortname()))

    def save(self, object_definition, message):
        """ Commits object_definition.get_filename() if it has any changes.
        This function is called by :py:class:`pynag.Model.EventHandlers`

        Args:

            object_definition (pynag.Model.ObjectDefinition): object to commit changes

            message (str): git commit message as specified in  ``git commit -m``

        """
        filename = object_definition.get_filename()
        if len(self.messages) > 0:
            message = [message, '\n'] + self.messages
            message = '\n'.join(message)
        self._git_add(filename)
        if self.is_dirty(filename):
            self._git_commit(filename, message)
        self.messages = []

    def is_dirty(self, filename):
        """ Returns True if filename needs to be committed to git

        Args:

            filename (str): file to check
        """
        command = "git status --porcelain '%s'" % filename
        output = self._run_command(command)
        # Return True if there is any output
        return len(output) > 0

    def write(self, object_definition, message):
        """ This method is called whenever :py:class:`pynag.Model.EventHandlers`
        is called.

        Args:

            object_definition (pynag.Model.ObjectDefinition): Object to write to file.

            message (str): git commit message as specified in  ``git commit -m``
        """
        # When write is called ( something was written to file )
        # We will log it in a buffer, and commit when save() is called.
        self.messages.append(" * %s" % message)

    def revert(self, commit):
        """ Revert some existing commits works like "git revert" """
        commit = commit.replace(r"'", r"\'")
        command = "git revert --no-edit -- '%s'" % commit
        return self._run_command(command)

    def commit(self, message='commited by pynag', filelist=None, author=None):
        """ Commit files with "git commit"

        Args:

            message (str): Message used for the git commit

            filelist (list of strings): List of filenames to commit (if None,
            then commit all files in the repo)

            author (str): Author to use for git commit. If any is specified,
            overwrite self.author_name and self.author_email

        Returns:
            stdout from the "git commit" shell command.

        """

        # Lets escape all single quotes from the message
        message = message.replace("'", r"\'")

        if author is None:
            author = "%s <%s>" % (self.author_name, self.author_email)

        # Escape all single quotes in author:
        author = author.replace("'", r"\'")

        if filelist is None:
            # If no files provided, commit everything
            self.add('.')
            command = "git commit -a -m '%s' --author='%s'" % (message, author)
            return self._run_command(command=command)
        elif isinstance(filelist, str):
            # in case filelist was provided as a string, consider to be only
            # one file
            filelist = [filelist]

        # Remove from commit list files that have not changed:
        filelist = [x for x in filelist if self.is_dirty(x)]

        # Run "git add" on every file. Just in case they are untracked
        self.ignore_errors = True
        for i in filelist:
            self.add(i)
        self.ignore_errors = False

        # Change ['file1','file2'] into the string """ 'file1' 'file2' """
        filestring = ''

        # Escape all single quotes in filenames
        filelist = [x.replace("'", r"\'") for x in filelist]

        # Wrap filename inside single quotes:
        filelist = ["'%s'" % x for x in filelist]

        # If filelist is empty, we have nothing to commit and we will return as
        # opposed to throwing error
        if not filelist:
            return
        # Create a space seperated string with the filenames
        filestring = ' '.join(filelist)
        command = "git commit -m '%s' --author='%s' -- %s" % (message, author, filestring)
        return self._run_command(command=command)

    def add(self, filename):
        """ Run git add on filename

        Args:
            filename (str): name of one file to add,

        Returns:
            str. The stdout from "git add" shell command.
        """

        # Escape all single quotes in filename:
        filename = filename.replace("'", r"\'")

        command = "git add -- '%s'" % filename
        return self._run_command(command)
