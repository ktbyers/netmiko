import re
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection

from netmiko.linux.linux_ssh import LinuxSSH
from netmiko.scp_handler import BaseFileTransfer


class ZpeNodegridSSH(LinuxSSH):
    def _enter_shell(self) -> str:
        """Enter the Bash shell on ZPE Nodegrid."""
        return self._send_command_str("shell", expect_string=r"[\$#]")

    def _return_cli(self) -> str:
        """Return to the ZPE Nodegrid CLI."""
        return self._send_command_str("exit", expect_string=r"[\$#]")


class ZpeNodegridFileTransfer(BaseFileTransfer):
    """ZPE Nodegrid SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: "BaseConnection",
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/var/tmp",
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

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        search_pattern = r"[\$#]"
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(self, remote_cmd: str = "", remote_file: Optional[str] = None) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(remote_cmd=remote_cmd, remote_file=remote_file)

    def remote_md5(self, base_cmd: str = "md5sum", remote_file: Optional[str] = None) -> str:
        """Calculate remote MD5 and returns the hash."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_cmd = f"{base_cmd} {self.file_system}/{remote_file}"
        self.ssh_ctl_chan._enter_shell()
        try:
            output = self.ssh_ctl_chan._send_command_str(
                remote_cmd, expect_string=r"[\$#]", read_timeout=300
            )
        finally:
            self.ssh_ctl_chan._return_cli()
        return self.process_md5(output.strip())

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"(\S+)\s+") -> str:
        """Process the string to retrieve the MD5 hash."""
        match = re.search(pattern, md5_output)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid output from MD5 command: {md5_output}")

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
