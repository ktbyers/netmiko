from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoS300SSH(CiscoSSHConnection):
    """
    Support for Cisco SG300 series of devices.

    Note, must configure the following to disable SG300 from prompting for username twice:

    configure terminal
    ip ssh password-auth
    """
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump\n")
        self.set_terminal_width(command='terminal width 511')
