import time
import re

from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class CheckPointGaiaSSH(NoConfig, BaseConnection):
    """
    Implements methods for communicating with Check Point Gaia
    firewalls.
    """

    prompt_pattern = r"[>#]"

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('>').
        """
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="set clienv rows 0")

        # Clear read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def command_echo_read(self, cmd: str, read_timeout: float) -> str:
        """Check Point clish double echoes the command (at least sometimes)"""

        re_cmd = re.escape(cmd)
        pattern = rf"{self.prompt_pattern}\s{re_cmd}"

        # Make sure you read until you detect the command echo (avoid getting out of sync)
        new_data = self.read_until_pattern(pattern=pattern, read_timeout=read_timeout)

        # There can be echoed prompts that haven't been cleared before the cmd echo
        # this can later mess up the trailing prompt pattern detection. Clear this out.
        lines = new_data.split(cmd)
        if len(lines) in [2, 3]:
            # lines[-1] should realistically just be the null string
            new_data = f"{cmd}{lines[-1]}"
        else:
            # cmd exists in the output multiple times? Just retain the original output
            pass

        return new_data

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        raise NotImplementedError
