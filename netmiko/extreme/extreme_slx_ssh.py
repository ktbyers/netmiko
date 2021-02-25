"""Support for Extreme SLX."""
import time
from typing import Any

from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeSlxSSH(CiscoSSHConnection):
    """Support for Extreme SLX."""

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on Extreme SLX."""
        return ""

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on Extreme Slx."""
        return ""

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
