"""SmartOptics DWDM is netmiko SSH class for SmartOptics DWDM devices."""

from netmiko.base_connection import BaseConnection


class SmartOpticsDWDMSSH(BaseConnection):
    def session_preparation(self):
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator="#",
        alt_prompt_terminator=">",
        delay_factor=1,
        pattern=None,
    ):
        return super().set_base_prompt(
            pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern
        )
