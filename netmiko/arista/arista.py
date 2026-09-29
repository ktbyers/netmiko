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
    supervisor_suffix_re = re.compile(r"\(s\d+\)")

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

    def _base_prompt_pattern(self, full_line: bool = False) -> str:
        """Return a pattern that consumes the complete Arista prompt."""
        base = re.escape(self.base_prompt)
        contexts = r"(?:\([^\r\n)]*\))*"
        tail = r".*$" if full_line else r"\s*$"
        return rf"{base}(?:\(s\d+\))?{contexts}{self.prompt_pattern}{tail}"

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Set ``base_prompt`` to the hostname without an ``(sN)`` suffix."""
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = self.supervisor_suffix_re.sub("", base_prompt)
        return self.base_prompt

    def read_until_prompt(
        self,
        read_timeout: float = 10.0,
        read_entire_line: bool = False,
        re_flags: int = 0,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read through the complete prompt, including supervisor context."""
        return self.read_until_pattern(
            pattern=self._base_prompt_pattern(full_line=read_entire_line),
            read_timeout=read_timeout,
            re_flags=re_flags,
            max_loops=max_loops,
        )

    def read_until_prompt_or_pattern(
        self,
        pattern: str = "",
        read_timeout: float = 10.0,
        read_entire_line: bool = False,
        re_flags: int = 0,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read through either a complete Arista prompt or ``pattern``."""
        prompt_pattern = self._base_prompt_pattern(full_line=read_entire_line)
        if pattern:
            pattern = rf"(?:{prompt_pattern}|{pattern})"
        else:
            pattern = prompt_pattern
        return self.read_until_pattern(
            pattern=pattern,
            read_timeout=read_timeout,
            re_flags=re_flags,
            max_loops=max_loops,
        )

    def _prompt_handler(self, auto_find_prompt: bool) -> str:
        """Return a complete prompt pattern for command reads."""
        if auto_find_prompt:
            try:
                prompt = self.find_prompt()
            except ValueError:
                return self._base_prompt_pattern()
            return re.escape(prompt.strip())
        return self._base_prompt_pattern()

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

        Arista dual-supervisor / stack members render the prompt as e.g.
        ``loc1-core01(s1)#`` / ``loc1-core01(s2)(config)#``. The historical
        implementation only stripped ``(s1)`` / ``(s2)`` verbatim; some
        platforms (7500R/7800R/EOS stacks) can render ``(s3)`` or higher, so
        we drop any ``(sN)`` before looking for the ``)#`` config marker.
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        output = self.supervisor_suffix_re.sub("", output)
        return check_string in output

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enter configuration mode and consume the complete prompt."""
        if not pattern:
            pattern = self._base_prompt_pattern()
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
