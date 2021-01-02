from typing import Any
import time
from netmiko.base_connection import BaseConnection


class RadETXBase(BaseConnection):
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
            output = self.send_command_timing(command_string=cmd)
            if confirm_response:
                output += self.send_command_timing(confirm_response)
            else:
                # Send enter by default
                output += self.send_command_timing(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self.send_command(command_string=cmd)
        assert isinstance(output, str)
        return output

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """The Rad ETX software does not have an enable."""
        return True

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """The Rad ETX software does not have an enable."""
        return ""

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """The Rad ETX software does not have an enable."""
        return ""

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
        self, check_string: str = ">config", pattern: str = ""
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
        username_pattern: str = r"(?:user>)",
        alt_prompt_term: str = r"#\s*$",
        **kwargs: Any
    ) -> str:
        """
        RAD presents with the following on login

        user>

        password> ****
        """
        self.TELNET_RETURN = self.RETURN
        output = super().telnet_login(
            username_pattern=username_pattern,
            alt_prompt_terminator=alt_prompt_term,
            **kwargs
        )
        assert isinstance(output, str)
        return output
