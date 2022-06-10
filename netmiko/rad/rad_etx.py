import time
from typing import Any

from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection


class RadETXBase(NoEnable, BaseConnection):
    """RAD ETX Support, Tested on RAD 203AX, 205A and 220A."""

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="config term length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self, cmd: str = "admin save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config Using admin save."""
        if confirm:
            output = self._send_command_timing_str(command_string=cmd)
            if confirm_response:
                output += self._send_command_timing_str(confirm_response)
            else:
                # Send enter by default
                output += self._send_command_timing_str(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self._send_command_str(command_string=cmd)
        return output

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = ">config",
        re_flags: int = 0,
    ) -> str:
        """Enter into configuration mode on remote device."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = ">config",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Rad config starts with baseprompt>config.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def exit_config_mode(
        self, exit_config: str = "exit all", pattern: str = "#"
    ) -> str:
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)


class RadETXSSH(RadETXBase):
    """RAD ETX SSH Support."""

    def __init__(self, **kwargs: Any) -> None:
        # Found that a global_delay_factor of 2 is needed at minimum for SSH to the Rad ETX.
        kwargs.setdefault("global_delay_factor", 2)
        return super().__init__(**kwargs)


class RadETXTelnet(RadETXBase):
    """RAD ETX Telnet Support."""

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r"#\s*$",
        username_pattern: str = r"(?:user>)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """
        RAD presents with the following on login

        user>

        password> ****
        """
        self.TELNET_RETURN = self.RETURN
        return super().telnet_login(
            username_pattern=username_pattern,
            alt_prompt_terminator=alt_prompt_terminator,
            pri_prompt_terminator=pri_prompt_terminator,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
