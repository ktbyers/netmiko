from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoTelnetConnection


class ExtremeExosSSH(CiscoSSHConnection):
    """Extreme EXOS support."""
    def session_preparation(self):
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")
        self.set_terminal_width(command='configure cli columns 256')

    def enable(self, *args, **kwargs):
        """No enable mode on Extreme EXOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Extreme EXOS."""
        pass


class ExtremeExosTelnet(CiscoTelnetConnection):
    """Extreme EXOS support."""
    def session_preparation(self):
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")
        self.set_terminal_width(command='configure cli columns 256')

    def enable(self, *args, **kwargs):
        """No enable mode on Extreme EXOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Extreme EXOS."""
        pass
