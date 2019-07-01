"""MRV Communications Driver (LX)."""
from __future__ import unicode_literals
import time
import re

from netmiko.cisco_base_connection import CiscoSSHConnection


class MrvLxSSH(CiscoSSHConnection):
    """MRV Communications Driver (LX)."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>|>>]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no pause")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string=">>"):
        """MRV has a >> for enable mode instead of # like Cisco"""
        return super(MrvLxSSH, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="assword", re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(MrvLxSSH, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def save_config(self, cmd="save config flash", confirm=False, confirm_response=""):
        """Saves configuration."""
        return super(MrvLxSSH, self).save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
