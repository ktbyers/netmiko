"""Ciena SAOS support."""
from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CienaSaosSSH(CiscoSSHConnection):
    """Ciena SAOS support."""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="system shell session set more off")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(self, *args, **kwargs):
        pass

    def save_config(self, cmd='', confirm=True, confirm_response=''):
        """Not Implemented"""
        raise NotImplementedError
