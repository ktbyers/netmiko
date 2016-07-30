"""Extreme support."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeSSH(CiscoSSHConnection):
    """Extreme support."""
    def session_preparation(self):
        """Extreme requires enable mode to disable paging."""
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")
