"""Subclass specific to Cisco FTD."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def __init__(self, *args, **kwargs):
        # FTD defaults to fast_cli=True and legacy_mode=False
        kwargs.setdefault("fast_cli", True)
        kwargs.setdefault("_legacy_mode", False)
        return super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()

    def send_config_set(self, *args, **kwargs):
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def enable(self, *args, **kwargs):
        """No enable mode on firepower ssh"""
        return ""

    def config_mode(self, *args, **kwargs):
        """No config mode on firepower ssh"""
        return ""

    def check_config_mode(self, *args, **kwargs):
        """No config mode on firepower ssh"""
        return False
