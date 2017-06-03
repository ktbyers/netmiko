"""Alcatel-Lucent Enterprise AOS support."""
from __future__ import print_function
from __future__ import unicode_literals
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class AlcatelAosSSH(CiscoSSHConnection):
    """Alcatel-Lucent Enterprise AOS support."""
    def session_preparation(self):
        # Prompt can be anything, but best practice is to end with > or #
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()

    def check_enable_mode(self, check_string='#'):
        """No enable mode on AOS"""
        pass

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE):
        """No enable mode on AOS"""
        pass

    def exit_enable_mode(self, exit_command='disable'):
        """No enable mode on AOS"""
        pass

    def check_config_mode(self, check_string=')#', pattern=''):
        """No config mode on AOS"""
        pass

    def config_mode(self, config_command='config term', pattern=''):
        """No config mode on AOS"""
        pass

    def exit_config_mode(self, exit_config='end', pattern=''):
        """No config mode on AOS"""
        pass

