"""Enterasys support."""
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class EnterasysSSH(CiscoSSHConnection):
    """Enterasys support."""
    def session_preparation(self):
        """Enterasys requires enable mode to disable paging."""
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="set length 0\n")

    def enable(self, *args, **kwargs):
        """Enterasys SecureStack must be in 'router' mode to have enable."""
        try:
            super(EnterasysSSH, self).enable(*args, **kwargs)
        except ValueError:
            prompt = self.find_prompt()
            if 'router' in prompt:
                raise
