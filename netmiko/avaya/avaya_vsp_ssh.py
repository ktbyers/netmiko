"""Avaya Virtual Services Platform Support."""
from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class AvayaVspSSH(CiscoSSHConnection):
    """Avaya Virtual Services Platform Support."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal more disable")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='save config', confirm=False):
        """Save Config"""
        return super(AvayaVspSSH, self).save_config(cmd=cmd, confirm=confirm)
