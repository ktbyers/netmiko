"""Ruijie RGOS Support"""
import time
from typing import Any

from netmiko.cisco_base_connection import CiscoBaseConnection


class RuijieOSBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        """Ruijie OS requires enable mode to set terminal width"""
        self.enable()
        self.set_terminal_width(command="terminal width 256", pattern="terminal")
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save config: write"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class RuijieOSSSH(RuijieOSBase):

    pass


class RuijieOSTelnet(RuijieOSBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
