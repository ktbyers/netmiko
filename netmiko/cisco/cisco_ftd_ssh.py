"""Subclass specific to Cisco FTD."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def send_config_set(self, config_commands=None):
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def enable(self):
        """no enable mode on firepower ssh"""
        raise AttributeError

    def config_mode(self, config_command="", pattern=""):
        """No Config mode on firepower ssh"""
        return ""

    def check_config_mode(self, check_string="", pattern=""):
        """No Config mode on firepower ssh"""
        return False
