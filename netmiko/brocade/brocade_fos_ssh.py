from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeFOSSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Brocade Fabric OS support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
