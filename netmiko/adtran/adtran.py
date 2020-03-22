import time
import re
from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
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

    def _read_channel_expect(self, *args, **kwargs):
        output = super()._read_channel_expect()
        
        #Strip backspaces for long commands
        output = self.strip_backspaces(output)
        return output

class AdtranOSSSH(AdtranOSBase):
    pass
