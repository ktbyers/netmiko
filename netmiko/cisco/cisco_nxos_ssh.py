from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoNxosSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def normalize_linefeeds(self, a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r'(\r\r\n|\r\n)')
        return newline.sub(self.RESPONSE_RETURN, a_string).replace('\r', '')
