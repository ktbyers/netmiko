"""MRV Communications Driver (OptiSwitch)."""
from __future__ import unicode_literals
import re

from netmiko.cisco_base_connection import CiscoSSHConnection


class MrvOptiswitchSSH(CiscoSSHConnection):
    """MRV Communications Driver (OptiSwitch)."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="no cli-paging")

    def enable(self, cmd='enable', pattern=r'#', re_flags=re.IGNORECASE):
        """Enable mode on MRV uses no password."""
        output = ""
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output
