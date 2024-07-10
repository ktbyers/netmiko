"""Alcatel-Lucent Enterprise AOS support (AOS6 and AOS8)."""

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class AlcatelAosSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Alcatel-Lucent Enterprise AOS support (AOS6 and AOS8)."""

    def session_preparation(self) -> None:
        # Prompt can be anything, but best practice is to end with > or #
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def save_config(
        self,
        cmd: str = "write memory flash-synchro",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
