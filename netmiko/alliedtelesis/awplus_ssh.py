"""Allied Telesis Support"""
import re
import os
from netmiko.cisco_base_connection import CiscoSSHConnection, CiscoFileTransfer


class AWplusSSH(CiscoSSHConnection):
    pass


class AWplusFileTransfer(CiscoFileTransfer):
    def __init__(
        self, ssh_conn, source_file, dest_file, file_system="flash:", direction="put",
    ):
        return super(AWplusFileTransfer, self).__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
        )

        if file_system:
            self.file_system = file_system
        else:
            raise ValueError("Destination file system must be specified")

        if direction == "put":
            self.source_md5 = self.file_md5(source_file)
            self.file_size = os.stat(source_file).st_size
        elif direction == "get":
            self.source_md5 = self.remote_md5(remote_file=source_file)
            self.file_size = self.remote_file_size(remote_file=source_file)
        else:
            raise ValueError("Invalid direction specified")

    def check_file_exists(self, remote_cmd="dir flash:"):
        """Check if the dest_file already exists on the file system."""
        if self.direction == "put":
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"{}".format(self.dest_file)
            return bool(re.search(search_string, remote_out, flags=re.DOTALL))
        elif self.direction == "get":
            return os.path.exists(self.dest_file)

    def process_md5(md5_output, pattern=None):
        raise NotImplementedError

    def remote_md5(self, base_cmd=None, remote_file=None):
        raise NotImplementedError

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
