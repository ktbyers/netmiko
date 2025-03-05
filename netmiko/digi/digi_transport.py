"""Digi TransPort Routers"""

from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class DigiTransportBase(NoEnable, NoConfig, CiscoSSHConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def save_config(
        self,
        cmd: str = "config 0 save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        output = self._send_command_str(
            command_string=cmd, expect_string="Please wait..."
        )
        return output


class DigiTransportSSH(DigiTransportBase):
    pass
