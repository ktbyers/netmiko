"""SmartOptics DWDM is netmiko SSH class for SmartOptics DWDM devices."""

from typing import Optional
from netmiko.base_connection import BaseConnection


class SmartOpticsDWDMSSH(BaseConnection):
    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern
        )
