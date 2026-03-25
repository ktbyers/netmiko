"""Calix Exa SSH Driver for Netmiko"""

from typing import Any, Optional

from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig


class CalixExaBase(BaseConnection, NoEnable, NoConfig):
    def session_preparation(self) -> Any:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        self.disable_paging(command="disable session pager")

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )


class CalixExaSSH(CalixExaBase):
    pass


class CalixExaTelnet(CalixExaBase):
    pass
