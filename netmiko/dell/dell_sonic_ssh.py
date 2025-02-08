"""
Dell EMC PowerSwitch platforms running Enterprise SONiC Distribution by Dell Technologies Driver
- supports dellenterprisesonic.
"""

from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer
from typing import Any, Optional
import os
import re


class DellSonicSSH(NoEnable, CiscoSSHConnection):
    """
    Dell EMC PowerSwitch platforms running Enterprise SONiC Distribution
    by Dell Technologies Driver - supports dellenterprisesonic.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>$#]")
        # Enter the sonic-cli
        self._enter_cli()
        self.disable_paging()
        self.set_base_prompt(alt_prompt_terminator="$")

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = r"\#",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_cli(self) -> str:
        """Enter the sonic-cli."""
        return self._send_command_str("sonic-cli", expect_string=r"\#")

    def _return_shell(self) -> str:
        """Return to the Linux shell."""
        return self._send_command_str("exit", expect_string=r"\$")


class DellSonicFileTransfer(BaseFileTransfer):
    """Dell EMC Networking SONiC SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: DellSonicSSH,
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
        self.ssh_ctl_chan: DellSonicSSH = ssh_conn

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

        # Go back to the Linux shell
        self.ssh_ctl_chan._return_shell()
        if not remote_cmd:
            remote_cmd = f"ls -l {self.file_system}/{remote_file}"
        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
        for line in remote_out.splitlines():
            if remote_file in line:
                file_size = line.split()[4]
                break
        self.ssh_ctl_chan._enter_cli()
        if "No such file or directory" in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def remote_space_available(self, search_pattern: str = r"Available") -> int:
        """Return space available on remote device."""
        # Go back to the Linux shell
        self.ssh_ctl_chan._return_shell()
        remote_cmd = f"df {self.file_system}"
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd)
        for line in remote_output.splitlines():
            if "root-overlay" in line:
                space_available = line.split()[3]
                break
        self.ssh_ctl_chan._enter_cli()
        return int(space_available)

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"(.*) (.*)") -> str:
        """Process the md5 output and return the hash."""
        return BaseFileTransfer.process_md5(md5_output, pattern=pattern)

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
        self.ssh_ctl_chan._return_shell()
        remote_md5_cmd = f"md5sum {self.file_system}/{remote_file}"
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=300)
        dest_md5 = self.process_md5(dest_md5)
        self.ssh_ctl_chan._enter_cli()
        return dest_md5.strip()

    def check_file_exists(self, remote_cmd: str = "dir home:/") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
            search_string = rf"{self.dest_file}"
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
