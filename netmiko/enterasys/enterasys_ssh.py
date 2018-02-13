"""Enterasys support."""
from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class EnterasysSSH(CiscoSSHConnection):
    """Enterasys support."""
    def session_preparation(self):
        """Enterasys requires enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="set length 0")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='', confirm=True, confirm_response=''):
        """Not Implemented"""
        raise NotImplementedError
