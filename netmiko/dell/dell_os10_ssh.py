"""Dell EMC Networking OS10 Driver - supports dellos10."""

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer
import os
import re


class DellOS10SSH(CiscoSSHConnection):
    """Dell EMC Networking OS10 Driver - supports dellos10."""

    def save_config(
        self,
        cmd="copy running-configuration startup-configuration",
        confirm=False,
        confirm_response="",
    ):
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class DellOS10FileTransfer(BaseFileTransfer):
    """Dell EMC Networking OS10 SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn,
        source_file,
        dest_file,
        file_system="/home/admin",
        direction="put",
        **kwargs,
    ):
        super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )
        self.folder_name = "/config"

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_cmd = f'system "ls -l {self.file_system}/{remote_file}"'
        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
        for line in remote_out.splitlines():
            if remote_file in line:
                file_size = line.split()[4]
                break
        if "Error opening" in remote_out or "No such file or directory" in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def remote_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Return space available on remote device."""
        remote_cmd = f'system "df {self.folder_name}"'
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        for line in remote_output.splitlines():
            if self.folder_name in line:
                space_available = line.split()[-3]
                break
        return int(space_available)

    @staticmethod
    def process_md5(md5_output, pattern=r"(.*) (.*)"):
        return super(DellOS10FileTransfer, DellOS10FileTransfer).process_md5(
            md5_output, pattern=r"(.*) (.*)"
        )

    def remote_md5(self, base_cmd="verify /md5", remote_file=None):
        """Calculate remote MD5 and returns the hash. """
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f'system "md5sum {self.file_system}/{remote_file}"'
        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=1500)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5.strip()

    def check_file_exists(self, remote_cmd="dir home"):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"Directory contents .*{}".format(self.dest_file)
            return bool(re.search(search_string, remote_out, flags=re.DOTALL))
        elif self.direction == "get":
            return os.path.exists(self.dest_file)

    def put_file(self):
        """SCP copy the file from the local system to the remote device."""
        destination = f"{self.dest_file}"
        self.scp_conn.scp_transfer_file(self.source_file, destination)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def get_file(self):
        """SCP copy the file from the remote device to local system."""
        source_file = f"{self.source_file}"
        self.scp_conn.scp_get_file(source_file, self.dest_file)
        self.scp_conn.close()
