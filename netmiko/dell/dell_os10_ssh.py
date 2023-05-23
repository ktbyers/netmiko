"""Dell EMC Networking OS10 Driver - supports dellos10."""
from typing import Any, Optional
from netmiko.base_connection import BaseConnection
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer
import os
import re


class DellOS10SSH(CiscoSSHConnection):
    """Dell EMC Networking OS10 Driver - supports dellos10."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def save_config(
        self,
        cmd: str = "copy running-configuration startup-configuration",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class DellOS10FileTransfer(BaseFileTransfer):
    """Dell EMC Networking OS10 SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/home/admin",
        direction: str = "put",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )
        self.folder_name = "/config"

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
            else:
                raise ValueError("self.direction is set to an invalid value")
        remote_cmd = f'system "ls -l {self.file_system}/{remote_file}"'
        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
        for line in remote_out.splitlines():
            if remote_file in line:
                file_size = line.split()[4]
                break
        if "Error opening" in remote_out or "No such file or directory" in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def remote_space_available(self, search_pattern: str = r"(\d+) bytes free") -> int:
        """Return space available on remote device."""
        remote_cmd = f'system "df {self.folder_name}"'
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd)
        for line in remote_output.splitlines():
            if self.folder_name in line:
                space_available = line.split()[-3]
                break
        return int(space_available)

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"(.*) (.*)") -> str:
        return super(DellOS10FileTransfer, DellOS10FileTransfer).process_md5(
            md5_output, pattern=pattern
        )

    def remote_md5(
        self, base_cmd: str = "verify /md5", remote_file: Optional[str] = None
    ) -> str:
        """Calculate remote MD5 and returns the hash."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
            else:
                raise ValueError("self.direction is set to an invalid value")
        remote_md5_cmd = f'system "md5sum {self.file_system}/{remote_file}"'
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=300)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5.strip()

    def check_file_exists(self, remote_cmd: str = "dir home") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
            search_string = r"Directory contents .*{}".format(self.dest_file)
            return bool(re.search(search_string, remote_out, flags=re.DOTALL))
        elif self.direction == "get":
            return os.path.exists(self.dest_file)
        else:
            raise ValueError("self.direction is set to an invalid value")

    def put_file(self) -> None:
        """SCP copy the file from the local system to the remote device."""
        destination = f"{self.dest_file}"
        self.scp_conn.scp_transfer_file(self.source_file, destination)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def get_file(self) -> None:
        """SCP copy the file from the remote device to local system."""
        source_file = f"{self.source_file}"
        self.scp_conn.scp_get_file(source_file, self.dest_file)
        self.scp_conn.close()
