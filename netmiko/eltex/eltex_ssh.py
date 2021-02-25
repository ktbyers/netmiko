import time
from typing import Any

from netmiko.cisco_base_connection import CiscoSSHConnection


class EltexSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
