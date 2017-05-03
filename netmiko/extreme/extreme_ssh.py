"""Extreme support."""
from __future__ import unicode_literals

import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeSSH(CiscoSSHConnection):
    """Extreme support.

    Designed for EXOS >= 15.0
    """
    def session_preparation(self):
        """Extreme requires enable mode to disable paging."""
        self._test_channel_read()
        self.enable()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging\n")

    def set_base_prompt(self, *args, **kwargs):
        """
        Extreme attaches an id to the prompt. The id increases with every command.
        It needs to br stripped off to match the prompt. Eg.

            testhost.1 #
            testhost.2 #
            testhost.3 #

        If new config is loaded and not saved yet, a '* ' prefix appears before the
        prompt, eg.

            * testhost.4 #
            * testhost.5 #
        """
        cur_base_prompt = super(ExtremeSSH, self).set_base_prompt(*args, **kwargs)
        # Strip off any leading * or whitespace chars; strip off trailing period and digits
        match = re.search(r'[\*\s]*(.*)\.\d+', cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        else:
            return self.base_prompt

    def send_command(self, *args, **kwargs):
        """Extreme needs special handler here due to the prompt changes."""

        # Change send_command behavior to use self.base_prompt
        kwargs.setdefault('auto_find_prompt', False)

        # refresh self.base_prompt
        self.set_base_prompt()
        return super(ExtremeSSH, self).send_command(*args, **kwargs)

    def config_mode(self, config_command=''):
        """No configuration mode on Extreme."""
        return ''

    def check_config_mode(self, check_string='#'):
        """Checks whether in configuration mode. Returns a boolean."""
        return super(ExtremeSSH, self).check_config_mode(check_string=check_string)

    def exit_config_mode(self, exit_config=''):
        """No configuration mode on Extreme."""
        return ''
