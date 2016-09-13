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
        self.scp_conn.connect(hostname=self.ssh_ctl_chan.host,
                              port=self.ssh_ctl_chan.port,
                              username=self.ssh_ctl_chan.username,
                              password=self.ssh_ctl_chan.password,
                              key_filename=self.ssh_ctl_chan.key_file,
                              look_for_keys=self.ssh_ctl_chan.use_keys,
                              allow_agent=False,
                              timeout=self.ssh_ctl_chan.timeout)
        self.scp_client = scp.SCPClient(self.scp_conn.get_transport())

    def scp_transfer_file(self, source_file, dest_file):
        """
        Transfer file using SCP

        Must close the SCP connection to get the file to write to the remote
        filesystem.
        """
        self.scp_transfer_file_to_remote(source_file, dest_file)

    def scp_transfer_file_to_remote(self, local_file, remote_file):
        """
        Transfer file to the remote using SCP

        Must close the SCP connection to get the file to write to the remote
        filesystem.
        """
        self.scp_client.put(local_file, remote_file)

    def scp_transfer_file_from_remote(self, remote_file, local_file):
        """
        Transfer file from the remote using SCP

        """
        self.scp_client.get(remote_file, local_file)

    def close(self):
        """Close the SCP connection."""
        self.scp_conn.close()


class FileTransfer(object):
    """Class to manage SCP file transfer and associated SSH control channel.

    Allows for transfer to and from the local host.
    """
    def __init__(self, ssh_conn, local_file, remote_file, file_system=None,
                 local_dir=None):
        if local_file is None and local_dir is None:
            raise ValueError('local_dir cannot be None if local_file is None.')

        self.ssh_ctl_chan = ssh_conn

        #local_file can be None if transfering from remote
        if local_file is not None:
            if os.path.sep in local_file:
                if local_dir is not None:
                    self.local_dir = os.path.dirname(local_file)
                self.local_file = os.path.basename(local_file)
        else:
            # Use remote filename for local filename.
            self.local_file = remote_file

        if not hasattr(self,local_file):
            self.local_file = local_file
        if local_dir is None or not hasattr(self, local_dir):
            self.local_dir = '.' + os.path.sep
        self.remote_file = remote_file
        # local_file may not exist yet if the source is the remote file system.
        if os.path.isfile(self.local_file):
            self.get_local_file_info()
        if not file_system:
            self.file_system = self.ssh_ctl_chan._autodetect_fs()
        else:
            self.file_system = file_system

    def __enter__(self):
        """Context manager setup"""
        self.establish_scp_conn()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager cleanup."""
        self.close_scp_chan()
        if exc_type is not None:
            raise exc_type(exc_value)

    def get_local_file_info(self):
        self.local_md5 = self.file_md5(os.path.join(
            self.local_dir, self.local_file))
        src_file_stats = os.stat(self.local_file)
        self.local_file_size = src_file_stats.st_size

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
        if space_avail > self.local_file_size:
            return True
        return False

    def check_file_exists(self, remote_cmd=""):
        """Check if the remote_file exists on the remote file system (return boolean)."""
        if not remote_cmd:
            remote_cmd = "dir {0}/{1}".format(self.file_system, self.remote_file)
        remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        search_string = r"Directory of .*{0}".format(self.remote_file)
        if 'Error opening' in remote_out:
            return False
        elif re.search(search_string, remote_out):
            return True
        else:
            raise ValueError("Unexpected output from check_file_exists")

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

    def compare_md5(self, base_cmd='verify /md5', delay_factor=8):
        """Compare md5 of file on network device to md5 of local file"""
        dest_md5 = self.remote_md5(base_cmd=base_cmd)
        return self.local_md5 == dest_md5

    def remote_md5(self, base_cmd='verify /md5', delay_factor=8):
        """
        Calculate remote MD5 and return the checksum.

        This command can be CPU intensive on the remote device.
        """
        remote_md5_cmd = "{0} {1}{2}".format(base_cmd, self.file_system,
                                             self.remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command_expect(remote_md5_cmd)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    @property
    def _get_remote(self):
        remote = "{}{}".format(self.file_system, self.remote_file)
        if ':' not in remote:
            raise ValueError("Invalid remote file system specified %s",
                             remote)
        return remote

    def transfer_file(self):
        return self.transfer_file_to_remote()

    def transfer_file_to_remote(self):
        """SCP transfer local_file to remote device."""
        remote = self._get_remote
        local = os.path.join(self.local_dir, self.local_file)
        self.scp_conn.scp_transfer_file_to_remote(local, remote)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def transfer_file_from_remote(self, local_file=None):
        """SCP transfer local_file to remote device."""
        remote = self._get_remote
        if local_file is not None:
            self.local_file = local_file
        local = os.path.join(self.local_dir, self.local_file)
        self.scp_conn.scp_transfer_file_from_remote(remote, local)
        # Must close the SCP connection to get the file written (flush)
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
