"""Alcatel-Lucent SROS support."""
from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class AlcatelSrosSSH(CiscoSSHConnection):
    """Alcatel-Lucent SROS support."""
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="environment no more")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super(AlcatelSrosSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)(>.*)*#', cur_base_prompt)
        if match:
            # strip off >... from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(AlcatelSrosSSH, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command='disable'):
        """Exits enable (privileged exec) mode."""
        return super(AlcatelSrosSSH, self).exit_enable_mode(exit_command=exit_command)

    def config_mode(self, config_command='configure', pattern='#'):
        """ Enter into configuration mode on SROS device."""
        return super(AlcatelSrosSSH, self).config_mode(config_command=config_command,
                                                       pattern=pattern)

    def exit_config_mode(self, exit_config='exit all', pattern='#'):
        """ Exit from configuration mode."""
        return super(AlcatelSrosSSH, self).exit_config_mode(exit_config=exit_config,
                                                            pattern=pattern)

    def check_config_mode(self, check_string='config', pattern='#'):
        """ Checks if the device is in configuration mode or not. """
        return super(AlcatelSrosSSH, self).check_config_mode(check_string=check_string,
                                                             pattern=pattern)
