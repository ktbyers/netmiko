import time
import re
from typing import Any, Optional
from netmiko.base_connection import BaseConnection
from netmiko.vyos.vyos_ssh import VyOSSSH
from netmiko.scp_handler import BaseFileTransfer


class UbiquitiEdgeRouterSSH(VyOSSSH):
    """Implement methods for interacting with EdgeOS EdgeRouter network devices."""

    def _enter_shell(self) -> str:
        """Already in shell."""
        return ""

    def _return_cli(self) -> str:
        """The shell is the CLI."""
        return ""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512")
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config."""
        if confirm is True:
            raise ValueError("EdgeRouter does not support save_config confirmation.")
        output = self._send_command_str(command_string=cmd)
        if "Done" not in output:
            raise ValueError(f"Save failed with following errors:\n\n{output}")
        return output


class UbiquitiEdgeRouterFileTransfer(BaseFileTransfer):
    """Ubiquiti EdgeRouter SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: "BaseConnection",
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/",
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

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def remote_md5(
        self, base_cmd: str = "md5sum", remote_file: Optional[str] = None
    ) -> str:
        """Calculate remote MD5 and returns the hash."""
        return super().remote_md5(base_cmd=base_cmd, remote_file=remote_file)

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"(\S+)\s+") -> str:
        """Process the string to retrieve the MD5 hash"""
        match = re.search(pattern, md5_output)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid output from MD5 command: {md5_output}")
