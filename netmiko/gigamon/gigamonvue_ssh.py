"""
Gigamon GigaVUE support.

For use with Gigamon GigaVUE devices.

"""
from typing import Any
from netmiko.cisco_base_connection import CiscoSSHConnection


class GigamonVUESSH(CiscoSSHConnection):
    """Gigamon GigaVUE support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self.ansi_escape_codes = True
        self.set_base_prompt()
        self.disable_paging(command="no cli session paging enable")

    def check_config_mode(
        self,
        check_string: str = "(config) #",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Perle uses "(<devicename>) (config) #" as config prompt
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )
