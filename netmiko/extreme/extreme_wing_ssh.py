from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeWingSSH(CiscoSSHConnection):
    """Extreme WiNG support."""
    def session_preparation(self):
        """Pass banner motd if used, disable paging and set Max term width"""
        self._test_channel_read(pattern=">|#")
        self.set_base_prompt()
        self.disable_paging(command="no page")
        self.set_terminal_width(command='terminal width 512')
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()
