from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoTelnetConnection


class CiscoIosSSH(CiscoSSHConnection):
    """Cisco IOS SSH driver."""

    @staticmethod
    def autodetect(session):
        """
        """
        matches = ["Cisco IOS Software", "Cisco Internetwork Operating System Software"]
        try:
            response = session.send_command("show version | inc Cisco")
            for m in matches:
                if m in response:
                    return 99
        except:
            return 0
        return 0

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')


class CiscoIosTelnet(CiscoTelnetConnection):
    """Cisco IOS Telnet driver."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')
