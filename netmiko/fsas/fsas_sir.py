import time
import re
from typing import Optional

from netmiko.base_connection import BaseConnection


class FsasSirBase(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="terminal pager disable")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Checks if the device is in administrator mode or not."""
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "admin",
        pattern: str = r"Password",
        enable_pattern: Optional[str] = None,
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

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exits administrator mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "end", pattern: str = "#") -> str:
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def commit(
        self,
        cmd: str = "commit",
        read_timeout: float = 120.0,
    ) -> str:
        """Commit the candidate configuration."""
        self.config_mode()
        return self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = False,
        confirm_response: str = "",
        read_timeout: float = 120.0,
    ) -> str:
        """Saves Config."""
        if confirm is True:
            raise ValueError("Fsas Si-R does not support save_config confirmation.")
        self.config_mode()
        return self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )


class FsasSirSSH(FsasSirBase):
    """FsasSir SSH driver."""

    pass
