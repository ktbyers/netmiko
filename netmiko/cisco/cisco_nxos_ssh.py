from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoNxosSSH(CiscoSSHConnection):
    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Nexus 5020 required extra delay post login
        """
        time.sleep(2)
        self.clear_buffer()
        self.set_base_prompt()
        self.disable_paging()

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r'(\r\r\n|\r\n)')
        return newline.sub('\n', a_string).replace('\r', '')
