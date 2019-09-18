"""A10 support."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class A10SSH(CiscoSSHConnection):
    """A10 support."""

    def session_preparation(self):
        """A10 requires to be enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0")

        # Will not do anything without A10 specific command
        self.set_terminal_width()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
