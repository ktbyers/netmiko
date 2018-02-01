from __future__ import unicode_literals
import time
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
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump")
        self.set_terminal_width(command='terminal width 511')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)

    def save_config(self):
        """ Saves config """
        self.enable()
        output = self.send_command(command_string='write', expect_string='[Yes')
        output += self.send_command('Yes')
        return output
