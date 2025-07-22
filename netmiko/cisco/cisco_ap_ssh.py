"""Subclass specific to Cisco AP."""

from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoApSSH(NoConfig, CiscoBaseConnection):
    """Subclass specific to Cisco AP."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        cmd = "terminal width 132"
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()
        self.set_base_prompt()
