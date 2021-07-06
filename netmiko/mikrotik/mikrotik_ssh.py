from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


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


class MikrotikRouterOsSSH(MikrotikBase):
    """Mikrotik RouterOS SSH driver."""

    pass


class MikrotikSwitchOsSSH(MikrotikBase):
    """Mikrotik SwitchOS SSH driver."""

    pass
