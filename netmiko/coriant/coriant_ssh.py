
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class CoriantSSH(CiscoSSHConnection):
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()

    def check_enable_mode(self, *args, **kwargs):
        raise AttributeError("Coriant devices do not support enable mode!")

    def enable(self, *args, **kwargs):
        raise AttributeError("Coriant devices do not support enable mode!")

    def exit_enable_mode(self, *args, **kwargs):
        raise AttributeError("Coriant devices do not support enable mode!")

    def check_config_mode(self):
        """Coriant devices do not have a config mode."""
        return False

    def config_mode(self):
        """Coriant devices do not have a config mode."""
        return ''

    def exit_config_mode(self):
        """Coriant devices do not have a config mode."""
        return ''

    def set_base_prompt(self, pri_prompt_terminator=':', alt_prompt_terminator='>',
                        delay_factor=2):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        super(CoriantSSH, self).set_base_prompt(pri_prompt_terminator=pri_prompt_terminator,
                                                alt_prompt_terminator=alt_prompt_terminator,
                                                delay_factor=delay_factor)
        return self.base_prompt

    def save_config(self, cmd='', confirm=True, confirm_response=''):
        """Not Implemented"""
        raise NotImplementedError
