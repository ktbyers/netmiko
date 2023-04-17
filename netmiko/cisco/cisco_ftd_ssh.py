"""Subclass specific to Cisco FTD."""
from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def send_config_set(self, *args: Any, **kwargs: Any) -> str:
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Canot change config on FTD via ssh"""
        return False
