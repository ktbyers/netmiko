import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log


class AdtranOSBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

class AdtranOSSSH(AdtranOSBase):
    pass
