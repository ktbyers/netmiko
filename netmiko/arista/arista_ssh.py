from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer
from netmiko import log


class AristaSSH(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Arista, unfortunately, does this:
        loc1-core01(s1)#

        Can also be (s2)
        """
        log.debug("pattern: {0}".format(pattern))
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        log.debug("check_config_mode: {0}".format(repr(output)))
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        log.debug("check_config_mode: {0}".format(repr(output)))
        return check_string in output


class AristaFileTransfer(CiscoFileTransfer):
    """Arista SCP File Transfer driver."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system=None, direction='put'):
        msg = "Arista SCP Driver is under development and not fully implemented"
        raise NotImplementedError(msg)
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if file_system:
            self.file_system = file_system
        else:
            raise ValueError("Destination file system must be specified for Arista")

        # if direction == 'put':
        #    self.source_md5 = self.file_md5(source_file)
        #    self.file_size = os.stat(source_file).st_size
        # elif direction == 'get':
        #    self.source_md5 = self.remote_md5(remote_file=source_file)
        #    self.file_size = self.remote_file_size(remote_file=source_file)
        # else:
        #    raise ValueError("Invalid direction specified")

    def put_file(self):
        """SCP copy the file from the local system to the remote device."""
        destination = "{}/{}".format(self.file_system, self.dest_file)
        self.scp_conn.scp_transfer_file(self.source_file, destination)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def remote_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Return space available on remote device."""
        return super(AristaFileTransfer, self).remote_space_available(
            search_pattern=search_pattern
        )

    def verify_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Verify sufficient space is available on destination file system (return boolean)."""
        return super(AristaFileTransfer, self).verify_space_available(
            search_pattern=search_pattern
        )

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        raise NotImplementedError

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file

        if not remote_cmd:
            remote_cmd = "dir {}/{}".format(self.file_system, remote_file)

        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
        # Match line containing file name
        escape_file_name = re.escape(remote_file)
        pattern = r".*({}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            file_size = match.group(0)
            file_size = file_size.split()[0]

        if 'No such file or directory' in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    @staticmethod
    def process_md5(md5_output, pattern=r"= (.*)"):
        raise NotImplementedError

    def remote_md5(self, base_cmd='show file', remote_file=None):
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        remote_md5_cmd = "{} {}{} md5sum".format(base_cmd, self.file_system, remote_file)
        return self.ssh_ctl_chan.send_command(remote_md5_cmd, delay_factor=3.0)

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
