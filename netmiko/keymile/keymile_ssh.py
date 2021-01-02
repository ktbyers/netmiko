from typing import Any
import time

from netmiko.cisco.cisco_ios import CiscoIosBase


class KeymileSSH(CiscoIosBase):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("default_enter", "\r\n")
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use paging."""
        return ""

    def check_config_mode(self, *args: Any, **kwargs: Any) -> bool:
        """Keymile does not use config mode."""
        return True

    def config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use config mode."""
        return ""

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use config mode."""
        return ""

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """Keymile does not use enable mode."""
        return False

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use enable mode."""
        return ""

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """Keymile does not use enable mode."""
        return ""

    def strip_prompt(self, a_string: str) -> str:
        """Remove appending empty line and prompt from output"""
        a_string = a_string[:-1]
        return super().strip_prompt(a_string=a_string)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
    ) -> str:
        """ set prompt termination to >"""
        return super().set_base_prompt(pri_prompt_terminator=pri_prompt_terminator)
