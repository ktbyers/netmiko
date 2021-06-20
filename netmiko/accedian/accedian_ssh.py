import time
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class AccedianSSH(NoEnable, NoConfig, CiscoSSHConnection):
    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self, pri_prompt_terminator=":", alt_prompt_terminator="#", delay_factor=2
    ):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        return self.base_prompt

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
