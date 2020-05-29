"""Subclass specific to Cisco Viptela."""
import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoViptelaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco Viptela."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="paginate false")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=")#", pattern="#"):
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, cmd="commit", confirm=False, confirm_response=""):
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
