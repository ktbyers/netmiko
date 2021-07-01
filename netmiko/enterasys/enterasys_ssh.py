"""Enterasys support."""
from typing import Any
from netmiko.cisco_base_connection import CiscoSSHConnection


class EnterasysSSH(CiscoSSHConnection):
    """Enterasys support."""

    def session_preparation(self) -> None:
        """Enterasys requires enable mode to disable paging."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        self.disable_paging(command="set length 0")

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
