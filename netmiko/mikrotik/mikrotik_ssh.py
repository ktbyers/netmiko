from typing import Any
import re
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import ReadTimeout


class MikrotikBase(NoEnable, CiscoSSHConnection):
    """Common Methods for Mikrotik RouterOS and SwitchOS"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"

        self._in_config_mode = False

        return super().__init__(**kwargs)

    def session_preparation(self, *args: Any, **kwargs: Any) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[\]>]")
        self.set_base_prompt()

    def _modify_connection_params(self) -> None:
        """Append login options to username
        c: disable console colors
        e: enable dumb terminal mode
        t: disable auto detect terminal capabilities
        w511: set term width
        h4098: set term height
        """
        self.username += "+cetw511h4098"

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Microtik does not have paging by default."""
        return ""

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """No save command, all configuration is atomic"""
        return ""

    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        """No configuration mode on Microtik"""
        self._in_config_mode = True
        return ""

    def check_config_mode(self, check_string: str = "", pattern: str = "") -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return self._in_config_mode

    def exit_config_mode(self, exit_config: str = ">", pattern: str = "") -> str:
        """No configuration mode on Microtik"""
        self._in_config_mode = False
        return ""

    def command_echo_read(self, cmd: str, read_timeout: float) -> str:
        """
                Mikrotik has some odd behavior where it repaints both the command and the line

                This could result in the command being at the top of the output multiple times
                (once for the actual echo and once for the repainting).

                Correct this behavior.

                Example output:

        DEBUG:netmiko:write_channel: b'ping count=5 1.0.0.1\r\n'
        DEBUG:netmiko:read_channel: ping count=5 1.0.0.1
        [admin@hostname] > ping count=5 1.0.0.1

          SEQ HOST                                     SIZE TTL TIME  STATUS
            0 1.0.0.1                                    56  60 23ms

        """

        # First read--initial command echo
        _ = self.read_until_pattern(pattern=re.escape(cmd), read_timeout=read_timeout)
        try:
            # Now try to read the re-painted line if it exists
            # Use a short timeout in case it is not there.
            _ = self.read_until_pattern(pattern=re.escape(cmd), read_timeout=1.5)
        except ReadTimeout:
            # No second re-paint of cmd?
            pass

        # Just return cmd and nothing after it.
        # This is different than normal Netmiko behavior
        return cmd


class MikrotikRouterOsSSH(MikrotikBase):
    """Mikrotik RouterOS SSH driver."""

    pass


class MikrotikSwitchOsSSH(MikrotikBase):
    """Mikrotik SwitchOS SSH driver."""

    pass
