"""Ciena SAOS support."""
from __future__ import print_function
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class CienaSaosSSH(CiscoSSHConnection):
    """Ciena SAOS support."""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="system shell session set more off\n")

    def enable(self, *args, **kwargs):
        pass
