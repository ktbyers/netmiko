from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class AristaSSH(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    def special_login_handler(self, delay_factor=1):
        """
        Arista adds a "Last login: " message that doesn't always have sufficient time to be handled
        """
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(3 * delay_factor)
        self.clear_buffer()
