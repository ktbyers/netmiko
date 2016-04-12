"""Extreme support."""
from netmiko.ssh_connection import SSHConnection


class ExtremeSSH(SSHConnection):
    """Extreme support."""
    def session_preparation(self):
        """Extreme requires enable mode to disable paging."""
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")
