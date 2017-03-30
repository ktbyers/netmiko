from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoTelnetConnection


class ExtremeWingSSH(CiscoSSHConnection):
    """Extreme WiNG support."""
    def session_preparation(self):
        self.set_base_prompt(pri_prompt_terminator='>',
                             alt_prompt_terminator='#')
        self.disable_paging(command="no page\n")
        self.set_terminal_width(command='terminal width 512')


class ExtremeWingTelnet(CiscoTelnetConnection):
    """Extreme WiNG support."""
    def session_preparation(self):
        self.set_base_prompt(pri_prompt_terminator='>',
                             alt_prompt_terminator='#')
        self.disable_paging(command="no page\n")
        self.set_terminal_width(command='terminal width 512')
