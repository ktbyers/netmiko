"""
Aruba OS support.

For use with Aruba OS Controllers.

"""
from typing import Any
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        # Aruba has an auto-complete on space behavior that is problematic
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Aruba OS requires enable mode to disable paging."""
        # Aruba switches output ansi codes
        self.ansi_escape_codes = True

        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(1 * delay_factor)
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no paging")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(
        self, check_string: str = "(config) #", pattern: str = ""
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
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
