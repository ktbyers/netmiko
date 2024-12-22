from typing import Any, Optional, TYPE_CHECKING, Union, Sequence, Iterator, TextIO
import os
import re

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer
from netmiko.exceptions import ReadTimeout

LINUX_PROMPT_PRI = os.getenv("NETMIKO_LINUX_PROMPT_PRI", "$")
LINUX_PROMPT_ALT = os.getenv("NETMIKO_LINUX_PROMPT_ALT", "#")
LINUX_PROMPT_ROOT = os.getenv("NETMIKO_LINUX_PROMPT_ROOT", "#")


class LinuxSSH(CiscoSSHConnection):
    prompt_pattern = rf"[{re.escape(LINUX_PROMPT_PRI)}{re.escape(LINUX_PROMPT_ALT)}]"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()

    def _enter_shell(self) -> str:
        """Already in shell."""
        return ""

    def _return_cli(self) -> str:
        """The shell is the CLI."""
        return ""

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Linux doesn't have paging by default."""
        return ""

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        if pattern is None:
            pattern = self.prompt_pattern
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = LINUX_PROMPT_PRI,
        alt_prompt_terminator: str = LINUX_PROMPT_ALT,
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Determine base prompt."""
        if pattern is None:
            pattern = self.prompt_pattern
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = True,
        **kwargs: Any,
    ) -> str:
        """Can't exit from root (if root)"""
        if self.username == "root":
            exit_config_mode = False
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def check_config_mode(
        self,
        check_string: str = LINUX_PROMPT_ROOT,
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Verify root"""
        return self.check_enable_mode(check_string=check_string)

    def config_mode(
        self,
        config_command: str = "sudo -s",
        pattern: str = "ssword",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Attempt to become root."""
        return self.enable(cmd=config_command, pattern=pattern, re_flags=re_flags)

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        return self.exit_enable_mode(exit_command=exit_config)

    def check_enable_mode(self, check_string: str = LINUX_PROMPT_ROOT) -> bool:
        """Verify root"""
        return super().check_enable_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_pattern(pattern=exit_command)
            output += self.read_until_pattern(pattern=self.prompt_pattern)
            # Nature of prompt might change with the privilege deescalation
            self.set_base_prompt(pattern=self.prompt_pattern)
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def enable(
        self,
        cmd: str = "sudo -s",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Attempt to become root."""
        msg = """

Netmiko failed to elevate privileges.

Please ensure you pass the sudo password into ConnectHandler
using the 'secret' argument and that the user has sudo
permissions.

"""

        output = ""
        if check_state and self.check_enable_mode():
            return output

        self.write_channel(self.normalize_cmd(cmd))

        # Failed "sudo -s" will put "#" in output so have to delineate further
        root_prompt = rf"(?m:{LINUX_PROMPT_ROOT}\s*$)"
        prompt_or_password = rf"({root_prompt}|{pattern})"
        output += self.read_until_pattern(pattern=prompt_or_password)
        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.normalize_cmd(self.secret))
            try:
                output += self.read_until_pattern(pattern=root_prompt)
            except ReadTimeout:
                raise ValueError(msg)
        # Nature of prompt might change with the privilege escalation
        self.set_base_prompt(pattern=root_prompt)
        if not self.check_enable_mode():
            raise ValueError(msg)
        return output

    def cleanup(self, command: str = "exit") -> None:
        """Try to Gracefully exit the SSH session."""
        return super().cleanup(command=command)

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError


class LinuxFileTransfer(CiscoFileTransfer):
    """
    Linux SCP File Transfer driver.

    Mostly for testing purposes.
    """

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
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    def remote_md5(
        self, base_cmd: str = "md5sum", remote_file: Optional[str] = None
    ) -> str:
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} {self.file_system}/{remote_file}"
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=300)
        dest_md5 = self.process_md5(dest_md5.strip()).strip()
        return dest_md5

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"^(\S+)\s+") -> str:
        return super(LinuxFileTransfer, LinuxFileTransfer).process_md5(
            md5_output, pattern=pattern
        )

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
