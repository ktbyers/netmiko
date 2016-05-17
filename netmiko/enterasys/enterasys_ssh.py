"""Enterasys support."""
from netmiko.ssh_connection import SSHConnection


class EnterasysSSH(SSHConnection):
    """Enterasys support."""
    def session_preparation(self):
        """Enterasys requires enable mode to disable paging."""
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="set length 0\n")
