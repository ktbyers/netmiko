from __future__ import unicode_literals
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoNxosSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r'(\r\r\n|\r\n)')
        return newline.sub('\n', a_string).replace('\r', '')
