"""Extreme Virtual Services Platform Support."""

from netmiko.extreme.extreme_ers_ssh import ExtremeErsSSH


class ExtremeVspSSH(ExtremeErsSSH):
    """Extreme Virtual Services Platform Support.

    Note, inherits from ExtremeErsSSH so that VSP can re-use 'CNTL-Y'
    special_login_handler.

    """

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
