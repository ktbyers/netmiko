"""Generic Terminal Server driver."""
from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection


class TerminalServer(BaseConnection):
    """Generic Terminal Server driver.

    Allow direct write_channel / read_channel operations without session_preparation causing
    an exception.
    """
    def session_preparation(self):
        """Do nothing here; base_prompt is not set; paging is not disabled."""
        pass


class TerminalServerSSH(TerminalServer):
    """Generic Terminal Server driver SSH."""
    pass


class TerminalServerTelnet(TerminalServer):
    """Generic Terminal Server driver telnet."""
    pass
