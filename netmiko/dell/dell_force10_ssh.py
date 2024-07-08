"""Dell Force10 Driver - supports DNOS9."""

from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
