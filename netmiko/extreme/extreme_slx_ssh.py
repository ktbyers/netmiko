"""Support for Extreme SLX."""

import time
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeSlxSSH(NoEnable, CiscoSSHConnection):
    """Support for Extreme SLX."""

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"#")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Adding a delay after login."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.write_channel(self.RETURN)
        time.sleep(1 * delay_factor)

    def save_config(
        self,
        cmd: str = "copy running-config startup-config",
        confirm: bool = True,
        confirm_response: str = "y",
    ) -> str:
        """Save Config for Extreme SLX."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
