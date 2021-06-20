"""Subclass specific to Cisco FTD."""
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()

    def send_config_set(self, *args, **kwargs):
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def check_config_mode(self, check_string: str = "", pattern: str = "") -> bool:
        """Canot change config on FTD via ssh"""
        return False
