"""
Aruba AOS CX support.

For use with Aruba AOS CX devices.

"""

from typing import Any
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaCxSSH(CiscoSSHConnection):
    """Aruba AOS CX support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="no page")

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure term",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Aruba auto completes on space so 'configure' needs fully spelled-out."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )
