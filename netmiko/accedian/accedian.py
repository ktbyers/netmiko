
from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class AccedianSSH(CiscoSSHConnection):
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Accedian."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Accedian."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Accedian."""
        pass

    def config_mode(self):
        """No config mode on Accedian."""
        pass

    def exit_config_mode(self):
        """No config mode on Accedian."""
        pass

    def set_base_prompt(self, pri_prompt_terminator=':', alt_prompt_terminator='#',
                        delay_factor=1):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        super(AccedianSSH, self).set_base_prompt(pri_prompt_terminator=pri_prompt_terminator,
                                                 alt_prompt_terminator=alt_prompt_terminator,
                                                 delay_factor=delay_factor)
        return self.base_prompt
