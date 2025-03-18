import time

from typing import Any, Dict, Optional
from netmiko.cisco_base_connection import CiscoSSHConnection

USER_MODE_REGEX = r"^.*%" # DEVNAME %
CONFIG_MODE_REGEX = r"^.*\* %" # DEVNAME* %

class AvaraSSH(CiscoSSHConnection):
    """Avara SSH Driver for Netmiko."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Avara SSH driver."""
        default_enter = kwargs.get("default_enter", "\r\n")
        kwargs["default_enter"] = default_enter
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=USER_MODE_REGEX)
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(
        self, check_string: str = "* %", pattern: str = CONFIG_MODE_REGEX
    ) -> bool:
        """Check if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "enable", pattern: str = CONFIG_MODE_REGEX
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config: str = "disable", pattern: str = USER_MODE_REGEX) -> str:
        """Exit configuration mode"""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def send_config_set(
        self,
        config_commands: Any = None,
        exit_config_mode: bool = True,
        **kwargs: Any
    ) -> str:
        """Send configuration commands to the device."""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            **kwargs
        )

    def save_config(
        self, cmd: str = "save flash", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save the configuration to non-volatile memory."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )