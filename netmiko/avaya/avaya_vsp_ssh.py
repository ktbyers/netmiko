"""Avaya Virtual Services Platform Support."""
from __future__ import print_function
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class AvayaVspSSH(CiscoSSHConnection):
    """Avaya Virtual Services Platform Support."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging(command="terminal more disable\n")
