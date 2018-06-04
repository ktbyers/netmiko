"""ZTE."""

from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log
import re


class ZTESSH(CiscoSSHConnection):

    """Alcatel-Lucent Enterprise AOS support (AOS6 and AOS8)."""
    def session_preparation(self):
        self.RETURN = '\r\n'
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()

        ## Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

        self.enable()

    """Base Class for cisco-like behavior."""
    def check_enable_mode(self, check_string='#'):
        """Check if in enable mode. Return boolean."""
        return super(ZTESSH, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd='enable', pattern='Please input password:', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(ZTESSH, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command='disable'):
        """Exits enable (privileged exec) mode."""
        return super(ZTESSH, self).exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        return super(ZTESSH, self).check_config_mode(check_string=check_string,
                                                                  pattern=pattern)

    def config_mode(self, config_command='configure', pattern=''):
        """
        Enter into configuration mode on remote device.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(ZTESSH, self).config_mode(config_command=config_command,
                                                            pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern=''):
        """Exit from configuration mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(ZTESSH, self).exit_config_mode(exit_config=exit_config,
                                                                 pattern=pattern)
    def save_config(self, *args, **kwargs):
        """Save Config"""
        return ''
