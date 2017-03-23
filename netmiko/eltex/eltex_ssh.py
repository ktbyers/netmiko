from __future__ import print_function
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class EltexSSH(CiscoSSHConnection):
    def session_preparation(self):
        """
        Prepare the session after the connection has been established
        """
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command='terminal datadump')
