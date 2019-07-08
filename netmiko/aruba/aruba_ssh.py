"""Aruba OS support"""
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super(ArubaSSH, self).__init__(**kwargs)

    def session_preparation(self):
        """ Aruba OS requires enable mode to disable paging.
        TODO: Explore why send_command() doesn't perform well but 
        send_command_timing() works as expected ???
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(1 * delay_factor)
        output = ""
        count = 1
        while count <= 30:
            output += self.read_channel()
            if 'any key to continue' in output:
                self.write_channel(self.RETURN)
                break
            else:
                time.sleep(.33 * delay_factor)
            count += 1

        # Try one last time to past "Press any key to continue
        self.write_channel(self.RETURN)

        # HP and HP Aruba switches  output contains VT100 escape codes
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        command = self.RETURN + "no page"
        self.send_command_timing(command)
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()
        # self.enable()

    def check_config_mode(self, check_string="(config) #", pattern=""):
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(ArubaSSH, self).check_config_mode(
            check_string=check_string, pattern=pattern
        )
