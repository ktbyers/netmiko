import time
from typing import Any, Optional

from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class PluribusSSH(NoConfig, BaseConnection):
    """Common methods for Pluribus."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._config_mode = False

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Make sure paging is disabled."""
        return super().disable_paging(command=command, delay_factor=delay_factor, cmd_verify=cmd_verify, pattern=pattern)

    def session_preparation(self) -> None:
        """Prepare the netmiko session."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
