import re
import time
from typing import Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection

CONFIG_PROMPT: str = "* %"
USER_MODE_REGEX: str = r"\s%"  # `DEVNAME % `
CONFIG_MODE_REGEX: str = r"\*\s%"  # `DEVNAME* % `


class AvaraSSH(CiscoSSHConnection):
    """Avara SSH Driver for Netmiko."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=USER_MODE_REGEX)
        # Clear the read buffer
        # time.sleep(0.3 * self.global_delay_factor)
        # self.clear_buffer()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "",
        enable_pattern: Optional[str] = r"[Pp]assword:",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode.

        Args:
            cmd: Command to enter enable mode
            pattern: Pattern to search for password prompt
            enable_pattern: Pattern to search for enable mode prompt
            re_flags: Regular expression flags

        Returns:
            str: Output of entering enable mode
        """
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def check_config_mode(
        # self, check_string=CONFIG_PROMPT, pattern=CONFIG_MODE_REGEX
        self,
        check_string: str = CONFIG_PROMPT,
        pattern: str = CONFIG_MODE_REGEX,
        force_regex: bool = True,
    ) -> bool:
        """Check if the device is in configuration mode"""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    # def config_mode(
    #     self, config_command="enable", pattern=CONFIG_MODE_REGEX
    # ) -> str:
    #     """Enter configuration mode."""
    #     return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="disable", pattern=USER_MODE_REGEX) -> str:
        """Exit configuration mode"""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def send_config_set(
        self, config_commands: Any = None, exit_config_mode: bool = True, **kwargs: Any
    ) -> str:
        """Send configuration commands to the device."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def save_config(
        self, cmd: str = "save flash", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save the configuration to non-volatile memory."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
