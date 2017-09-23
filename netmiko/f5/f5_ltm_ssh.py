from __future__ import unicode_literals
import time
from netmiko.base_connection import BaseConnection


class F5LtmSSH(BaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        self._test_channel_read()
        self.set_base_prompt()
        command = "{}set length 0{}".format(self.RETURN, self.RETURN)
        self.disable_paging(command=command)
        time.sleep(1 * delay_factor)
        self.tmsh_mode()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def tmsh_mode(self, delay_factor=1):
        """tmsh command is equivalent to config command on F5."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        command = "{}tmsh{}".format(self.RETURN, self.RETURN)
        self.write_channel(command)
        time.sleep(1 * delay_factor)
        self.clear_buffer()
        return None
