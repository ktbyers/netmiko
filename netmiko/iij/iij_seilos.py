"""IIJ SEIL OS device support (currently tested on SEIL/x86 Ayame)."""

import re
import time
from typing import Any

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class IIJSeilosBase(NoEnable, NoConfig, BaseConnection):
    """Common methods for IIJ SEIL OS devices."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"#")
        self.set_base_prompt()
        self.disable_paging(command="environment pager off")
        self.set_terminal_width(command="environment terminal column 511")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """Strip ANSI escape codes including DEC private mode sequences."""
        output = super().strip_ansi_escape_codes(string_buffer)
        # DEC private mode set: ESC[?<n>h (e.g. ESC[?1h for cursor key mode)
        output = re.sub(r"\x1b\[\?\d+h", "", output)
        # DECKPAM/DECKPNM: ESC= and ESC>
        output = re.sub(r"\x1b[=>]", "", output)
        return output

    def save_config(
        self,
        cmd: str = "save-to flashrom",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save the running configuration to flash memory."""
        return self._send_command_str(command_string=cmd)


class IIJSeilosSSH(IIJSeilosBase):
    """IIJ SEIL OS SSH driver."""

    pass


class IIJSeilosTelnet(IIJSeilosBase):
    """IIJ SEIL OS Telnet driver."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
