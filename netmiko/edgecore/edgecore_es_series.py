# -*- encoding: utf-8 -*-
"""Netmiko support for Edge-Core ES series switches."""
from __future__ import print_function
from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoTelnetConnection


class EdgeCoreTelnet(CiscoTelnetConnection):

    def session_preparation(self):
        """Edge-Core requires enable mode to set terminal options."""
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 80')

    def config_mode(self, config_command='', pattern=''):
        """Enter configuration mode."""
        return super(EdgeCoreTelnet, self).config_mode(config_command='configure', pattern='')
