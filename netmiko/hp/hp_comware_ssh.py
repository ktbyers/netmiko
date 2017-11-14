from __future__ import print_function
from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
import re


class HPComwareSSH(CiscoSSHConnection):

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        self._test_channel_read(pattern=r'[>\]]')
        self.set_base_prompt()
        self.priv_escalation()
        self.disable_paging(command="\nscreen-length disable\n")

    def priv_escalation(self):
        """ Privilege Escalation before entering config mode """
        try:
            out_version = self.send_command_timing("display version")
            regex_v = re.compile(r"""Comware\s+Software,\s+Version\s+(.*),
            \sRelease\s+""", re.X)
            match_v = regex_v.search(out_version, re.I | re.M)
            self.send_command_timing('e')

            # Comware version 5.xx
            if match_v and match_v.group(1).startswith('5'):
                priv_escalation_cmd = 'super'
                self.send_command(
                        priv_escalation_cmd,
                        expect_string='Password:', auto_find_prompt=False)
                self.send_command(
                        self.secret,
                        expect_string='>', auto_find_prompt=False)
            # Comware version 7.xx
            elif match_v and match_v.group(1).startswith('7'):
                priv_escalation_cmd = 'super level-15'
                self.send_command(
                        priv_escalation_cmd,
                        expect_string='Username:', auto_find_prompt=False)
                self.send_command(
                        self.username,
                        expect_string='Password:', auto_find_prompt=False)
                self.send_command(
                        self.secret, expect_string='>', auto_find_prompt=False)
        except Exception as e:
            raise e

    def config_mode(self, config_command='system-view'):
        """Enter configuration mode."""
        return super(
                HPComwareSSH, self).config_mode(config_command=config_command)

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

        Should be set to something that is general and applies in multiple
        contexts. For Comware this will be the router prompt with < > or [ ]
        stripped off.

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
