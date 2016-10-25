"""A10 support."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class A10SSH(CiscoSSHConnection):
    """A10 support."""
    def session_preparation(self):
        """A10 requires to be enable mode to disable paging."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0\n")

        # Will not do anything without A10 specific command
        self.set_terminal_width()
