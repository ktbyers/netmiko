"""Enterasys support."""
from __future__ import unicode_literals
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class EnterasysSSH(CiscoSSHConnection):
    """Enterasys support."""
    def session_preparation(self):
        """Enterasys requires enable mode to disable paging."""
        self._test_channel_read()
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="set length 0\n")

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE):
        """Enterasys SecureStack must be in 'router' mode to have enable.

        This message is generated '% Invalid input detected at '^' marker.' if enable is
        not supported.
        """
        output = ""
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            # Check if enable command is not known (SecureStack not in 'router' mode)
            if '% Invalid input detected at' in output:
                return output
            self.write_channel(self.normalize_cmd(self.secret))
            output += self.read_until_prompt()
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output
