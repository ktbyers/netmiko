from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class VertivMPHBase(NoEnable, NoConfig, CiscoSSHConnection):
    """TODO"""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        # self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"cli->")
        self.set_base_prompt()

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def cleanup(self, command: str = "logout") -> None:
        """Return paging before disconnect"""
        return super().cleanup(command=command)


class VertivMPHSSH(VertivMPHBase):
    pass


"""class DlinkDSTelnet(VertivMPHBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
"""