from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer
from netmiko.scp_handler import SCPConn


class CiscoNxosSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def normalize_linefeeds(self, a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r'(\r\r\n|\r\n)')
        return newline.sub(self.RESPONSE_RETURN, a_string).replace('\r', '')


class CiscoNxosFileTransfer(CiscoFileTransfer):
    """Cisco NXOS SCP File Transfer driver."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system=None, direction='put'):
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if file_system:
            self.file_system = file_system
        else:
            raise ValueError("Destination file system must be specified for NX-OS")

#        if direction == 'put':
#            self.source_md5 = self.file_md5(source_file)
#            self.file_size = os.stat(source_file).st_size
#        elif direction == 'get':
#            self.source_md5 = self.remote_md5(remote_file=source_file)
#            self.file_size = self.remote_file_size(remote_file=source_file)
#        else:
#            raise ValueError("Invalid direction specified")

    def remote_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Return space available on remote device."""
        return super(CiscoNxosFileTransfer, self).remote_space_available(
            search_pattern=search_pattern
        )

    def verify_space_available(self, search_pattern=r"bytes total \((.*) bytes free\)"):
        """Verify sufficient space is available on destination file system (return boolean)."""
        raise NotImplementedError

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        raise NotImplementedError

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        raise NotImplementedError

    @staticmethod
    def process_md5(md5_output, pattern=r"= (.*)"):
        """
        Process the string to retrieve the MD5 hash

        Output from Cisco IOS (ASA is similar)
        .MD5 of flash:file_name Done!
        verify /md5 (flash:file_name) = 410db2a7015eaa42b1fe71f1bf3d59a2
        """
        raise NotImplementedError

    def compare_md5(self, base_cmd='verify /md5'):
        """Compare md5 of file on network device to md5 of local file"""
        raise NotImplementedError

    def remote_md5(self, base_cmd='verify /md5', remote_file=None):
        raise NotImplementedError

    def transfer_file(self):
        """SCP transfer file."""
        if self.direction == 'put':
            self.put_file()
        elif self.direction == 'get':
            self.get_file()

    def verify_file(self):
        """Verify the file has been transferred correctly."""
        raise NotImplementedError

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
