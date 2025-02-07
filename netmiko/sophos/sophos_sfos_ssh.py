"""SophosXG (SFOS) Firewall support"""

from typing import Any
import time
import os

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


SOPHOS_MENU_DEFAULT = os.getenv("NETMIKO_SOPHOS_MENU", "4")


class SophosSfosSSH(NoEnable, NoConfig, CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"Select Menu Number")
        """
        Sophos Firmware Version SFOS 18.0.0 GA-Build339

        Main Menu

            1.  Network  Configuration
            2.  System   Configuration
            3.  Route    Configuration
            4.  Device Console
            5.  Device Management
            6.  VPN Management
            7.  Shutdown/Reboot Device
            0.  Exit

            Select Menu Number [0-7]:
        """
        self.send_command_expect("\r", expect_string=r"Select Menu Number")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
