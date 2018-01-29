"""Dell Force10 Driver - supports DNOS9."""
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""

    def save_config(self, cmd='copy running-configuration startup-configuration', confirm=False):
        """Saves Config"""
        return super(DellForce10SSH, self).save_config(cmd=cmd, confirm=confirm)
