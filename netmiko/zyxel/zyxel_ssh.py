import re

from typing import Any, Sequence, Iterator, TextIO, Union
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig


class ZyxelSSH(NoEnable, NoConfig, CiscoSSHConnection):
    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """No paging on Zyxel"""
        return ""

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        enter_config_mode: bool = False,
        **kwargs: Any
    ) -> str:
        """No config mode on Zyxel"""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            enter_config_mode=enter_config_mode,
            **kwargs
        )

    def session_preparation(self) -> None:
        super().session_preparation()
        # Zyxel switches output ansi codes
        self.ansi_escape_codes = True

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """Replace '^J' code by next line"""
        output = re.sub(r"^\^J", self.RETURN, string_buffer)
        return super().strip_ansi_escape_codes(output)
