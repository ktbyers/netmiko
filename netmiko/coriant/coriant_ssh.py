import re
from typing import Any
from netmiko.cisco_base_connection import CiscoSSHConnection


class CoriantSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()

    def check_enable_mode(self, check_string: str = "") -> bool:
        """Platform does not have an enable mode."""
        return True

    def enable(
        self, cmd: str = "", pattern: str = "ssword", re_flags: int = re.IGNORECASE
    ) -> str:
        """Platform does not have an enable mode."""
        return ""

    def exit_enable_mode(self, exit_command: str = "") -> str:
        """Platform does not have an enable mode."""
        return ""

    def check_config_mode(self, check_string: str = "", pattern: str = "") -> bool:
        """Platform does not have a configuration mode."""
        return True

    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Platform does not have a configuration mode."""
        return ""

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """Devices do not have a config mode."""
        return ""

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ":",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 2.0,
    ) -> str:
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        return self.base_prompt

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
