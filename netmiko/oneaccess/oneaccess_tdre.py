"""Netmiko driver for OneAccess TDRE"""
import time
from typing import Any

from netmiko.base_connection import BaseConnection


class OneaccessTDREBase(BaseConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init connection - similar as Cisco"""
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        """Prepare connection - disable paging"""
        self._test_channel_read(pattern=r"[>]")
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not supported."""
        return ""


class OneaccessTDRESSH(OneaccessTDREBase):
    pass


class OneaccessTDRETelnet(OneaccessTDREBase):
    pass
