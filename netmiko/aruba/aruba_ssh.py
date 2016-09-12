"""Aruba OS support"""
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""
    def session_preparation(self):
        """Aruba OS requires enable mode to disable paging."""
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="no paging")
