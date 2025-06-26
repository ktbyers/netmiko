from typing import Any, Optional, Union, Sequence
from typing import TYPE_CHECKING
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer
from netmiko.exceptions import NetmikoTimeoutException

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection


class AristaBase(CiscoSSHConnection):
    prompt_pattern = r"[$>#]"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        try:
            cmd = "terminal width 511"
            self.set_terminal_width(command=cmd, pattern=r"Width set to")
        except NetmikoTimeoutException:
            # Continue on if setting 'terminal width' fails
            pass
        self.disable_paging(cmd_verify=False, pattern=r"Pagination disabled")
        self.set_base_prompt()

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        """
        Arista's sometimes duplicate the command echo if they fall behind.

        arista9-napalm#
        show version | json
        arista9-napalm#show version | json

        Using the terminating pattern tries to ensure that it is less likely they
        fall behind.
        """
        if not pattern:
            pattern = self.prompt_pattern
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = r"\#",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>\#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Arista, unfortunately, does this:
        loc1-core01(s1)#

        Can also be (s2)
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        return check_string in output

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Force arista to read pattern all the way to prompt on the next line."""

        if not re_flags:
            re_flags = re.DOTALL
        check_string = re.escape(")#")

        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
            pattern = f"{pattern}.*{check_string}"
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_shell(self) -> str:
        """Enter the Bourne Shell."""
        output = self._send_command_str("bash", expect_string=r"[\$#]")
        return output

    def _return_cli(self) -> str:
        """Return to the CLI."""
        output = self._send_command_str("exit", expect_string=r"[#>]")
        return output


class AristaSSH(AristaBase):
    pass


class AristaTelnet(AristaBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class AristaFileTransfer(CiscoFileTransfer):
    """Arista SCP File Transfer driver."""

    prompt_pattern = r"[$>#]"

    def __init__(
        self,
        ssh_conn: "BaseConnection",
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/mnt/flash",
        direction: str = "put",
        **kwargs: Any,
    ) -> None:
        return super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        search_pattern = self.prompt_pattern
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
        self, base_cmd: str = "verify /md5", remote_file: Optional[str] = None
    ) -> str:
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} file:{self.file_system}/{remote_file}"
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=600)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd: Union[str, Sequence[str], None] = None) -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: Union[str, Sequence[str], None] = None) -> None:
        raise NotImplementedError
