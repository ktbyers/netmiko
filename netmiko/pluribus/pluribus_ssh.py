from typing import Any, Optional
import time
from netmiko.base_connection import BaseConnection


class PluribusSSH(BaseConnection):
    """Common methods for Pluribus."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._config_mode = False

    def disable_paging(
        self,
        command: str = "pager off",
        delay_factor: float = 1.0,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Make sure paging is disabled."""
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def session_preparation(self) -> None:
        """Prepare the netmiko session."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, *args: Any, **kwargs: Any) -> bool:
        """
        Pluribus devices don't have a config mode.
        Therefore it can be considered as always in config mode.
        """
        return self._config_mode

    def config_mode(self, *args: Any, **kwargs: Any) -> str:
        """No special actions to enter in config mode."""
        self._config_mode = True
        return ""

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """No special actions to exit config mode."""
        self._config_mode = False
        return ""
