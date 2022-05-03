from typing import Optional
from paramiko import SSHClient
import time
from os import path
from netmiko.cisco_base_connection import CiscoBaseConnection

class CiscoUCMSSH(CiscoBaseConnection):
    """
    Implements methods for communicating with Cisco Unified Call Manager.
    """

    # def session_preparation(self) -> None:
    #     """
    #     Prepare the session after the connection has been established.
    #     """
    #     delay_factor = self.select_delay_factor(delay_factor=0)
    #     time.sleep(0.3 * delay_factor)
    #     self.clear_buffer()
    #     self._test_channel_read(pattern=r"admin:")
    #     self.set_base_prompt()
    #     self.enable()
    #     self.disable_paging()
    #     # Clear the read buffer
    #     time.sleep(0.3 * self.global_delay_factor)
    #     self.clear_buffer()
        
    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ":",
        alt_prompt_terminator: str = ":",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple
        contexts. For Cisco Unified Call Manager prompt with ':'.

        """
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern
            )
        