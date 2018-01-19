from __future__ import print_function
from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
import re


class HPComwareSSH(CiscoSSHConnection):

    def __init__(self, *args, enable_cmd=None, **kwargs):
        """ add another parameter enable_cmd ot HPcomwareSSH that depends on
        comware version """
        super().__init__(*args, **kwargs)
        self.enable_cmd = enable_cmd

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.
        Extra time to read HP banners.
        """
        self._test_channel_read(pattern=r'[>\]]')
        self.set_base_prompt()
        # Comware version matters ...
        self.com_version = self.get_comware_version()
        if self.com_version in '5':
            self.enable_cmd = 'super'
        elif self.com_version in '7':
            self.enable_cmd = 'super level-15'
        # check if screen-length disable is permitted by some TACACS/RADIUS
        # config and enable it after priviledge escalation "enable() method"
        if 'denied' in self.send_command_timing("screen-length disable"):
            self.enable()
        self.disable_paging(command="screen-length disable\n")

    def get_comware_version(self):
        """ send display version and grep Comware exact version """
        try:
            out_version = self.send_command_timing("display version")
            match_v = re.search(r'Comware\s+Software,\s+Version\s+(.*),\sRelease\s+', out_version, re.I | re.M)
            self.send_command_timing('e')
            # Comware version 5.xx
            if match_v and match_v.group(1).startswith('5'):
                return '5'
            # Comware version 7.xx
            elif match_v and match_v.group(1).startswith('7'):
                return '7'
            else:
                raise Exception
        except Exception as e:
            raise e

    def config_mode(self, config_command='system-view'):
        """Enter configuration mode."""
        return super(
                HPComwareSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='quit'):
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

    def enable(self):
        """enable mode on Comware depends on version 5/7."""
        try:
            # Comware version 5.xx
            if self.com_version == '5':
                self.send_command(
                        self.enable_cmd,
                        expect_string='Password:', auto_find_prompt=False)
                self.send_command(
                        self.secret,
                        expect_string='>', auto_find_prompt=False)
                return
            # Comware version 7.xx
            elif self.com_version == '7':
                self.send_command(
                        self.enable_cmd,
                        expect_string='Username:', auto_find_prompt=False)
                self.send_command(
                        self.username,
                        expect_string='Password:', auto_find_prompt=False)
                self.send_command(
                        self.secret, expect_string='>', auto_find_prompt=False)
                return
            else:
                raise("Unrecognised Comware Version")
        except Exception as e:
            raise e
        # return self.config_mode(config_command=self.enable_cmd)

    def exit_enable_mode(self, exit_command='quit'):
        """enable mode on Comware is system-view."""
        return self.exit_config_mode(exit_config=exit_command)

    def check_enable_mode(self, check_string=']'):
        """enable mode on Comware is system-view."""
        return self.check_config_mode(check_string=check_string)
