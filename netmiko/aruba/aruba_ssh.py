"""Aruba OS support"""
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""
    def session_preparation(self):
        """Aruba OS requires enable mode to disable paging."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(1 * delay_factor)
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no paging")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string='(config) #', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(ArubaSSH, self).check_config_mode(check_string=check_string,
                                                       pattern=pattern)
