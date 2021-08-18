import time
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class JuniperScreenOsSSH(NoEnable, NoConfig, BaseConnection):
    """
    Implement methods for interacting with Juniper ScreenOS devices.
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="set console page 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        return self._send_command_str(command_string=cmd)
