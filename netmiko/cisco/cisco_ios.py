from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoIosBase(CiscoBaseConnection):
    """Common Methods for IOS (both SSH and telnet)."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')


class CiscoIosSSH(CiscoBaseConnection):
    """Cisco IOS SSH driver."""
    pass


class CiscoIosTelnet(CiscoBaseConnection):
    """Cisco IOS Telnet driver."""
    pass
