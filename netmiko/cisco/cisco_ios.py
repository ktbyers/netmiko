from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoIosBase(CiscoBaseConnection):
    """Common Methods for IOS (both SSH and telnet)."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    @staticmethod
    def _autodetect(session, *args, **kwargs):
        cmd = "show version | inc Cisco"
        search_patterns = [
           "Cisco IOS Software",
           "Cisco Internetwork Operating System Software"
        ]
        return super(CiscoIosBase, self)._autodetect(session, cmd=cmd,
                                                     search_patterns=search_patterns)


class CiscoIosSSH(CiscoBaseConnection):
    """Cisco IOS SSH driver."""
    pass


class CiscoIosTelnet(CiscoBaseConnection):
    """Cisco IOS Telnet driver."""
    pass
