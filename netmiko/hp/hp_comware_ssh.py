from __future__ import print_function
from __future__ import unicode_literals

import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class HPComwareSSH(CiscoSSHConnection):

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(2 * delay_factor)
        self.clear_buffer()
        self.set_base_prompt()
        self.disable_paging(command="\nscreen-length disable\n")

    def config_mode(self, config_command='system-view'):
        """Enter configuration mode."""
        return super(HPComwareSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='return'):
        """Exit config mode."""
        return super(HPComwareSSH, self).exit_config_mode(exit_config=exit_config)

    def check_config_mode(self, check_string=']'):
        """Check whether device is in configuration mode. Return a boolean."""
        return super(HPComwareSSH, self).check_config_mode(check_string=check_string)

    def set_base_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']',
                        delay_factor=1):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """
        prompt = super(HPComwareSSH, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

        # Strip off leading character
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(self, cmd='system-view'):
        """enable mode on Comware is system-view."""
        return self.config_mode(config_command=cmd)

    def exit_enable_mode(self, exit_command='return'):
        """enable mode on Comware is system-view."""
        return self.exit_config_mode(exit_config=exit_command)

    def check_enable_mode(self, check_string=']'):
        """enable mode on Comware is system-view."""
        return self.check_config_mode(check_string=check_string)
