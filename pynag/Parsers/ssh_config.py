# -*- coding: utf-8 -*-
"""Experimental module for configuring remote nagios instance via ssh."""

import os
import stat
import tarfile
import io

from pynag.Parsers import config_parser


class SshConfig(config_parser.Config):

    """ Parse object configuration files from remote host via ssh

    Uses python-paramiko for ssh connections.
    """

    def __init__(self, host, username, password=None, cfg_file=None):
        """ Creates a SshConfig instance

        Args:

            host: Host to connect to

            username: User to connect with

            password: Password for `username`

            cfg_file: Nagios main cfg file
        """
        import paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password)
        self.ftp = self.ssh.open_sftp()

        import io
        c = io.StringIO()
        self.tar = tarfile.open(mode='w', fileobj=c)

        self.cached_stats = {}
        super(SshConfig, self).__init__(cfg_file=cfg_file)

    def open(self, filename, *args, **kwargs):
        """ Behaves like file.open only, via ssh connection """
        return self.tar.extractfile(filename)
        tarinfo = self._get_file(filename)
        string = tarinfo.tobuf()
        print(string)
        return io.StringIO(string)
        return self.tar.extractfile(tarinfo)

    def add_to_tar(self, path):
        """
        """
        print("Taring ", path)
        command = "find '{path}' -type f | tar -c -T - --to-stdout --absolute-names"
        command = command.format(path=path)
        print(command)
        stdin, stdout, stderr = self.ssh.exec_command(command, bufsize=50000)
        tar = tarfile.open(fileobj=stdout, mode='r|')
        if not self.tar:
            self.tar = tar
            # return
        else:
            for i in tar:
                self.tar.addfile(i)

    def is_cached(self, filename):
        if not self.tar:
            return False
        return filename in self.tar.getnames()

    def _get_file(self, filename):
        """ Download filename and return the TarInfo object """
        if filename not in self.tar.getnames():
            self.add_to_tar(filename)
        return self.tar.getmember(filename)

    def get_cfg_files(self):
        cfg_files = []
        for config_object, config_value in self.maincfg_values:

            # Add cfg_file objects to cfg file list
            if config_object == "cfg_file":
                config_value = self.abspath(config_value)
                if self.isfile(config_value):
                    cfg_files.append(config_value)
            elif config_object == "cfg_dir":
                absolut_path = self.abspath(config_value)
                command = "find '%s' -type f -iname \*cfg" % (absolut_path)
                stdin, stdout, stderr = self.ssh.exec_command(command)
                raw_filelist = stdout.read().splitlines()
                cfg_files += raw_filelist
            else:
                continue
            if not self.is_cached(config_value):
                self.add_to_tar(config_value)
        return cfg_files

    def isfile(self, path):
        """ Behaves like os.path.isfile only, via ssh connection """
        try:
            copy = self._get_file(path)
            return copy.isfile()
        except IOError:
            return False

    def isdir(self, path):
        """ Behaves like os.path.isdir only, via ssh connection """
        try:
            file_stat = self.stat(path)
            return stat.S_ISDIR(file_stat.st_mode)
        except IOError:
            return False

    def islink(self, path):
        """ Behaves like os.path.islink only, via ssh connection """
        try:
            file_stat = self.stat(path)
            return stat.S_ISLNK(file_stat.st_mode)
        except IOError:
            return False

    def readlink(self, path):
        """ Behaves like os.readlink only, via ssh connection """
        return self.ftp.readlink(path)

    def stat(self, *args, **kwargs):
        """ Wrapper around os.stat only, via ssh connection """
        path = args[0]
        if not self.is_cached(path):
            self.add_to_tar(path)
        if path not in self.tar.getnames():
            raise IOError("No such file or directory %s" % path)
        member = self.tar.getmember(path)
        member.st_mode = member.mode
        member.st_mtime = member.mtime
        return member

    def access(self, *args, **kwargs):
        """ Wrapper around os.access only, via ssh connection """
        return os.access(*args, **kwargs)

    def exists(self, path):
        """ Wrapper around os.path.exists only, via ssh connection """
        try:
            self.ftp.stat(path)
            return True
        except IOError:
            return False

    def listdir(self, *args, **kwargs):
        """ Wrapper around os.listdir  but via ssh connection """
        stats = self.ftp.listdir_attr(*args, **kwargs)
        for i in stats:
            self.cached_stats[args[0] + "/" + i.filename] = i
        files = [x.filename for x in stats]
        return files
