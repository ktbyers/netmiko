"""Dell Force10 Driver - supports DNOS9."""
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""

    def save_config(self):
        """Save Config on DellForce10SSH"""
        self.send_command('copy running-configuration startup-configuration')
