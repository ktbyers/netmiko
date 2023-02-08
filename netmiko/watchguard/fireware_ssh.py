import time
from typing import Any

from netmiko.base_connection import BaseConnection


class WatchguardFirewareSSH(BaseConnection):
    """
    Implements methods for communicating with Watchguard Firebox firewalls.
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('#').
        """
        self._test_channel_read()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "configure", pattern: str = r"\#", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "#") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """No save config on Watchguard."""
        return ""
