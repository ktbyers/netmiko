import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_exception import NetmikoAuthenticationException
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

    def strip_ansi_escape_codes(self, string_buffer):
        """
        Huawei does a strange thing where they add a space and then add ESC[1D
        to move the cursor to the left one.

		Adtran also encounters this same issue like Huawei when executing long commands...
		This function works as intended with Adtran also (Taken from Huawei)

        The extra space is problematic.
        """
        code_cursor_left = chr(27) + r"\[\d+D"
        output = string_buffer
        pattern = rf" {code_cursor_left}"
        output = re.sub(pattern, "", output)

        log.debug("Stripping ANSI escape codes")
        log.debug(f"new_output = {output}")
        log.debug(f"repr = {repr(output)}")
        return super().strip_ansi_escape_codes(output)

class AdtranOSSSH(AdtranOSBase):
	pass
