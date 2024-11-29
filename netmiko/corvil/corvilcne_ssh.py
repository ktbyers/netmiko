"""
Corvil CNE support.

For use with Corvil CNE devices.

"""
from typing import Any
from netmiko.cisco_base_connection import CiscoSSHConnection


class CorvilCNESSH(CiscoSSHConnection):
    """Corvil CNE support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self.ansi_escape_codes = True
        self._test_channel_read(pattern="$")
        self.disable_paging(command="terminal length 0")

    def check_config_mode(
        self,
        check_string: str = "(config) $",
        pattern: str = r"[$]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Corvil uses "<devicename>(config) $" as config prompt
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )
