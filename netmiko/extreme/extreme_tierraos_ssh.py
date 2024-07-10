"""Support for Extreme TierraOS."""

import time
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeTierraSSH(NoEnable, CiscoSSHConnection):
    """Support for Extreme TierraOS."""

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"#")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging(command="terminal length 0")

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Adding a delay after login."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.write_channel(self.RETURN)
        time.sleep(1 * delay_factor)

    def save_config(
        self,
        cmd: str = "copy run flash://config-file/startup-config",
        confirm: bool = False,
        confirm_response: str = "y",
    ) -> str:
        """Save Config for Extreme TierraOS."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
