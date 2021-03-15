"""Support for Extreme NOS/VDX."""
import re
import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeNosSSH(CiscoSSHConnection):
    """Support for Extreme NOS/VDX."""

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
        """Save Config for Extreme VDX."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
