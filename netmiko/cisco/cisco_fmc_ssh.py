"""Subclass specific to Cisco ASA."""

from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoFmcSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
