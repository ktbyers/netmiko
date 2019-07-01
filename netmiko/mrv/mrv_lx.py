"""MRV Communications Driver (LX)."""
from __future__ import unicode_literals
import time
import re

from netmiko.cisco_base_connection import CiscoSSHConnection


class MrvLxSSH(CiscoSSHConnection):
    """MRV Communications Driver (LX)."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>|>>]')
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no pause")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(self, cmd='enable', pattern=r'assword:', re_flags=re.IGNORECASE):
        '''MRV has a >> for enable mode instead of # like Cisco'''
        output = ""
        msg = "Failed to enter enable mode. Please ensure you pass " \
              "the 'secret' argument to ConnectHandler."
        if not self.check_enable_mode('>>'):
            self.write_channel(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            self.write_channel(self.normalize_cmd(self.secret))
            output += self.read_until_prompt()
            if not self.check_enable_mode('>>'):
                raise ValueError(msg)
        return output

    def save_config(self, cmd='save config flash', confirm=False):
        """Saves configuration."""
        return super(MrvLxSSH, self).save_config(cmd=cmd, confirm=confirm)
