"""Extreme support."""
import time
import re
from typing import Any, Union, List, Dict

from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeExosBase(CiscoSSHConnection):
    """Extreme Exos support.

    Designed for EXOS >= 15.0
    """

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging")
        self.send_command_timing("disable cli prompting")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
    ) -> str:
        """
        Extreme attaches an id to the prompt. The id increases with every command.
        It needs to br stripped off to match the prompt. Eg.

            testhost.1 #
            testhost.2 #
            testhost.3 #

        If new config is loaded and not saved yet, a '* ' prefix appears before the
        prompt, eg.

            * testhost.4 #
            * testhost.5 #
        """
        cur_base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

        # Strip off any leading * or whitespace chars; strip off trailing period and digits
        match = re.search(r"[\*\s]*(.*)\.\d+", cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        else:
            return self.base_prompt

    def send_command(
        self, *args: Any, **kwargs: Any
    ) -> Union[List[Any], Dict[str, Any], str]:
        """Extreme needs special handler here due to the prompt changes."""

        # Change send_command behavior to use self.base_prompt
        kwargs.setdefault("auto_find_prompt", False)

        # refresh self.base_prompt
        self.set_base_prompt()
        return super().send_command(*args, **kwargs)

    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Platform does not have a configuration mode."""
        return ""

    def check_config_mode(self, check_string: str = "#", pattern: str = "") -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """Platform does not have a configuration mode."""
        return ""

    def save_config(
        self,
        cmd: str = "save configuration primary",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class ExtremeExosSSH(ExtremeExosBase):
    pass


class ExtremeExosTelnet(ExtremeExosBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
