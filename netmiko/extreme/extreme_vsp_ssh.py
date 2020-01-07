"""Extreme Virtual Services Platform Support."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeVspSSH(CiscoSSHConnection):
    """Extreme Virtual Services Platform Support."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal more disable")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd="save config", confirm=False, confirm_response=""):
        """Save Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
