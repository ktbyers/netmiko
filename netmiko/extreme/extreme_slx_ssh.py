"""Support for Extreme SLX."""
import time
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeSlxSSH(NoEnable, CiscoSSHConnection):
    """Support for Extreme SLX."""

    def special_login_handler(self, delay_factor=1):
        """Adding a delay after login."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.write_channel(self.RETURN)
        time.sleep(1 * delay_factor)

    def save_config(
        self,
        cmd="copy running-config startup-config",
        confirm=True,
        confirm_response="y",
    ):
        """Save Config for Extreme SLX."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
