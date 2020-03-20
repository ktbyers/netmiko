"""Support for Extreme NOS/VDX."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeNosSSH(CiscoSSHConnection):
    """Support for Extreme NOS/VDX."""

    def enable(self, *args, **kwargs):
        """No enable mode on Extreme VDX."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Extreme VDX."""
        pass

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
        """Save Config for Extreme VDX."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
