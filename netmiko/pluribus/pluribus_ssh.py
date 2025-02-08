import time
from typing import Any, Optional

from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class PluribusSSH(NoConfig, BaseConnection):
    """Common methods for Pluribus."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._config_mode = False

    def session_preparation(self) -> None:
        """Prepare the netmiko session."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(
        self,
        command: str = "pager off",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging on Pluribus devices.

        :param command: Command to disable pagination of output
        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
        :param cmd_verify: Verify command echo before proceeding
        :param pattern: Pattern to terminate reading of channel
        """
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )
