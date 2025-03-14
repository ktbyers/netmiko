from typing import Any, Optional, Callable
import re
import os
from netmiko.base_connection import BaseConnection
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer


class CiscoNxosBase(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # NX-OS has an issue where it echoes the command even though it hasn't returned the prompt
        self._test_channel_read(pattern=r"[>#]")
        self.set_terminal_width(
            command="terminal width 511", pattern=r"terminal width 511"
        )
        self.disable_paging()
        self.set_base_prompt()

    def normalize_linefeeds(self, a_string: str) -> str:
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r"(\r\r\n\r|\r\r\n|\r\n)")
        # NX-OS fix for incorrect MD5 on 9K (due to strange <enter> patterns on NX-OS)
        return newline.sub(self.RESPONSE_RETURN, a_string).replace("\r", "\n")

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self,
        cmd: str = "copy running-config startup-config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        self.enable()

        output = ""
        if confirm:
            output += self._send_command_timing_str(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
            if confirm_response:
                output += self._send_command_timing_str(
                    confirm_response, strip_prompt=False, strip_command=False
                )
            else:
                # Send enter by default
                output += self._send_command_timing_str(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            # NX-OS is very slow on save_config ensure it waits long enough.
            output += self._send_command_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
                read_timeout=100,
            )
        return output


class CiscoNxosSSH(CiscoNxosBase):
    pass


class CiscoNxosTelnet(CiscoNxosBase):
    pass


class CiscoNxosFileTransfer(CiscoFileTransfer):
    """Cisco NXOS SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: str = "bootflash:",
        direction: str = "put",
        socket_timeout: float = 10.0,
        progress: Optional[Callable[..., Any]] = None,
        progress4: Optional[Callable[..., Any]] = None,
        hash_supported: bool = True,
    ) -> None:
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if hash_supported is False:
            raise ValueError("hash_supported=False is not supported for NX-OS")

        if file_system:
            self.file_system = file_system
        else:
            raise ValueError("Destination file system must be specified for NX-OS")

        if direction == "put":
            self.source_md5 = self.file_md5(source_file)
            self.file_size = os.stat(source_file).st_size
        elif direction == "get":
            self.source_md5 = self.remote_md5(remote_file=source_file)
            self.file_size = self.remote_file_size(remote_file=source_file)
        else:
            raise ValueError("Invalid direction specified")

        self.socket_timeout = socket_timeout
        self.progress = progress
        self.progress4 = progress4

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f"dir {self.file_system}{self.dest_file}"
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
            search_string = r"{}.*Usage for".format(self.dest_file)
            if "No such file or directory" in remote_out:
                return False
            elif re.search(search_string, remote_out, flags=re.DOTALL):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)
        else:
            raise ValueError("Invalid value for file transfer direction.")

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
                raise ValueError("Invalid value for file transfer direction.")

        if not remote_cmd:
            remote_cmd = f"dir {self.file_system}/{remote_file}"

        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
        if re.search("no such file or directory", remote_out, flags=re.I):
            raise IOError("Unable to find file on remote system")
        # Match line containing file name
        escape_file_name = re.escape(remote_file)
        pattern = r".*({}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            file_size = match.group(0)
            file_size = file_size.split()[0]
            return int(file_size)

        raise IOError("Unable to find file on remote system")

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"= (.*)") -> str:
        """Not needed on NX-OS."""
        raise NotImplementedError

    def remote_md5(
        self, base_cmd: str = "show file", remote_file: Optional[str] = None
    ) -> str:
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} {self.file_system}{remote_file} md5sum"
        output = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=300)
        output = output.strip()
        return output

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
