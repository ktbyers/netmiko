from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class QuantaMeshSSH(CiscoSSHConnection):
    def disable_paging(self, command="no pager", delay_factor=1):
        """Disable paging"""
        return super(QuantaMeshSSH, self).disable_paging(command=command)

    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(QuantaMeshSSH, self).config_mode(config_command=config_command)

    def save_config(self, cmd='', confirm=True, confirm_response=''):
        """Not Implemented"""
        raise NotImplementedError
