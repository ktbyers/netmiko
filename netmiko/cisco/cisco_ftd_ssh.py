"""Subclass specific to Cisco FTD."""
from netmiko.base_connection import NoChangesMixin
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFtdSSH(NoChangesMixin, CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
