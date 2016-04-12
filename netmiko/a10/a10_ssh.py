"""A10 support."""
from netmiko.ssh_connection import SSHConnection


class A10SSH(SSHConnection):
    """A10 support."""
    def session_preparation(self):
        """A10 requires to be enable mode to disable paging."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0\n")
