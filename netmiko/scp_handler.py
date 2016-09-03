"""
Create a SCP side-channel to transfer a file to remote network device.

SCP requires a separate SSH connection.

Currently only supports Cisco IOS and Cisco ASA.
"""

from __future__ import print_function
from __future__ import unicode_literals

import re
import os
import hashlib

import paramiko
import scp


class SCPConn(object):
    """Establish a secure copy channel to the remote network device."""
    def __init__(self, ssh_conn):
        self.ssh_ctl_chan = ssh_conn
        self.establish_scp_conn()

    def establish_scp_conn(self):
        """Establish the secure copy connection."""
        self.scp_conn = paramiko.SSHClient()
        self.scp_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.scp_conn.connect(hostname=self.ssh_ctl_chan.ip,
                              port=self.ssh_ctl_chan.port,
                              username=self.ssh_ctl_chan.username,
                              password=self.ssh_ctl_chan.password,
                              look_for_keys=False,
                              allow_agent=False,
                              timeout=8)
        self.scp_client = scp.SCPClient(self.scp_conn.get_transport())

    def scp_transfer_file(self, source_file, dest_file):
        """
        Transfer file using SCP

        Must close the SCP connection to get the file to write to the remote filesystem
        """
        self.scp_client.put(source_file, dest_file)

    def scp_fetch_file(self, source_file, dest_file):
        """
        Fetch file using SCP
        """
        self.scp_client.get(source_file, dest_file)

    def close(self):
        """Close the SCP connection."""
        self.scp_conn.close()


class FileTransfer(object):
    """Class to manage SCP file transfer and associated SSH control channel."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system=None, direction='put'):
        if direction is 'put':
            self.ssh_ctl_chan = ssh_conn
            self.source_file = source_file
            self.source_md5 = self.file_md5(source_file)
            self.dest_file = dest_file
            src_file_stats = os.stat(source_file)
            self.file_size = src_file_stats.st_size
            if not file_system:
                self.file_system = self.ssh_ctl_chan._autodetect_fs()
            else:
                self.file_system = file_system
        else:
            if not file_system:
                self.file_system = self.ssh_ctl_chan._autodetect_fs()
            else:
                self.file_system = file_system
            self.ssh_ctl_chan = ssh_conn
            self.source_file = source_file
            self.source_md5 = self.remote_md5(remote_file=source_file)
            self.file_size = self.remote_file_size(remote_file=source_file)
            self.dest_file = dest_file

    def __enter__(self):
        """Context manager setup"""
        self.establish_scp_conn()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager cleanup."""
        self.close_scp_chan()
        if exc_type is not None:
            raise exc_type(exc_value)

    def establish_scp_conn(self):
        """Establish SCP connection."""
        self.scp_conn = SCPConn(self.ssh_ctl_chan)

    def close_scp_chan(self):
        """Close the SCP connection to the remote network device."""
        self.scp_conn.close()
        self.scp_conn = None

    def verify_space_available(self, search_pattern=r"bytes total \((.*) bytes free\)"):
        """Verify sufficient space is available on remote network device (return boolean)."""
        remote_cmd = "dir {0}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        match = re.search(search_pattern, remote_output)
        space_avail = int(match.group(1))
        if space_avail > self.file_size:
            return True
        return False

    def verify_local_space(self):
        destination_stats = os.statvfs(".")
        free_space = destination_stats.f_bsize * destination_stats.f_bavail
        if free_space > self.file_size:
            return True
        return False

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file exists on the remote file system (return boolean)."""
        if not remote_cmd:
            remote_cmd = "dir {0}/{1}".format(self.file_system, self.dest_file)
        remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        search_string = r"Directory of .*{0}".format(self.dest_file)
        if 'Error opening' in remote_out:
            return False
        elif re.search(search_string, remote_out):
            return True
        else:
            raise ValueError("Unexpected output from check_file_exists")

    def remote_file_size(self, remote_cmd="", remote_file=None, delay_factor=8):
        """ Get the file size of the remote file. """
        if remote_file is None:
            remote_file = self.dest_file
        if not remote_cmd:
            remote_cmd = "dir {0}/{1}".format(self.file_system, remote_file)
        remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        # Cisco devices show the file size and then the date with the month first
        size_month = re.search('([0-9]+\s+[A-Z][a-z][a-z])', remote_out).group(1)
        size = re.search('([0-9]+)', size_month).group(1)
        if 'Error opening' in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(size)

    @staticmethod
    def file_md5(file_name):
        """Compute MD5 hash of file."""
        with open(file_name, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.md5(file_contents).hexdigest()
        return file_hash

    @staticmethod
    def process_md5(md5_output, pattern=r"= (.*)"):
        """
        Process the string to retrieve the MD5 hash

        Output from Cisco IOS (ASA is similar)
        .MD5 of flash:file_name Done!
        verify /md5 (flash:file_name) = 410db2a7015eaa42b1fe71f1bf3d59a2
        """
        match = re.search(pattern, md5_output)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid output from MD5 command: {0}".format(md5_output))

    def compare_md5(self, base_cmd='verify /md5', delay_factor=1):
        """Compare md5 of file on network device to md5 of local file"""
        dest_md5 = self.remote_md5(base_cmd=base_cmd)
        return self.source_md5 == dest_md5

    def remote_md5(self, base_cmd='verify /md5', remote_file=None, delay_factor=1):
        """
        Calculate remote MD5 and return the checksum.

        This command can be CPU intensive on the remote device.
        """
        if remote_file is None:
            remote_file = self.dest_file
        remote_md5_cmd = "{0} {1}{2}".format(base_cmd, self.file_system, remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command_expect(remote_md5_cmd)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def transfer_file(self):
        """SCP transfer source_file to remote device."""
        destination = "{}{}".format(self.file_system, self.dest_file)
        if ':' not in destination:
            raise ValueError("Invalid destination file system specified")
        self.scp_conn.scp_transfer_file(self.source_file, destination)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def fetch_file(self):
        """ SCP copy the file from the remote device to local system. """
        self.scp_conn.scp_fetch_file(self.source_file, self.dest_file)
        self.scp_conn.close()

    def verify_file(self):
        """Verify the file has been transferred correctly."""
        return self.compare_md5()

    def enable_scp(self, cmd=None):
        """
        Enable SCP on remote device.

        Defaults to Cisco IOS command
        """
        if cmd is None:
            cmd = ['ip scp server enable']
        elif not hasattr(cmd, '__iter__'):
            cmd = [cmd]
        self.ssh_ctl_chan.send_config_set(cmd)

    def disable_scp(self, cmd=None):
        """
        Disable SCP on remote device.

        Defaults to Cisco IOS command
        """
        if cmd is None:
            cmd = ['no ip scp server enable']
        elif not hasattr(cmd, '__iter__'):
            cmd = [cmd]
        self.ssh_ctl_chan.send_config_set(cmd)
