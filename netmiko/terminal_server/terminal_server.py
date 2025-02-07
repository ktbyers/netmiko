"""Generic Terminal Server driver."""

from typing import Any

from netmiko.base_connection import BaseConnection


class TerminalServer(BaseConnection):
    """Generic Terminal Server driver.

    Allow direct write_channel / read_channel operations without session_preparation causing
    an exception.
    """

    def session_preparation(self) -> None:
        """Do nothing here; base_prompt is not set; paging is not disabled."""
        pass


class TerminalServerSSH(TerminalServer):
    """Generic Terminal Server driver SSH."""

    pass


class TerminalServerTelnet(TerminalServer):
    """Generic Terminal Server driver telnet."""

    def telnet_login(self, *args: Any, **kwargs: Any) -> str:
        # Disable automatic handling of username and password when using terminal server driver
        return ""

    def std_login(self, *args: Any, **kwargs: Any) -> str:
        return super().telnet_login(*args, **kwargs)
