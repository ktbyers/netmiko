"""Extreme Virtual Services Platform Support."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeVspSSH(CiscoSSHConnection):
    """Extreme Virtual Services Platform Support."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="terminal more disable")

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
