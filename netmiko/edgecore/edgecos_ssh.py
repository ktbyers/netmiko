"""EdgeCOS support."""
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection

class EdgecosSSH(CiscoSSHConnection):
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0")

        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

