# -*- encoding: utf-8 -*-
"""Netmiko support for Edge-Core ES series switches."""
from __future__ import print_function
from __future__ import unicode_literals
import re

from netmiko.cisco_base_connection import CiscoTelnetConnection


class EdgeCoreTelnet(CiscoTelnetConnection):

    def set_base_prompt(self, *args, **kwargs):
        """
        Remove tty number from the prompt.
        It depends of how many connections are active on moment of connection.
        switch-0> switch-1> switch-2> ...
        """
        cur_base_prompt = super(EdgeCoreTelnet, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)-\d+', cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        return cur_base_prompt

    def session_preparation(self):
        """Edge-Core requires enable mode to set terminal options."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 80')
        self.exit_enable_mode()

    def config_mode(self, config_command='', pattern=''):
        """Enter configuration mode."""
        return super(EdgeCoreTelnet, self).config_mode(config_command='configure', pattern='')
