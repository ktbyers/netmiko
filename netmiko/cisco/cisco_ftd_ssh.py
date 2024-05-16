"""Subclass specific to Cisco FTD."""
from typing import Any
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection
import re

class CiscoFtdSSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Subclass specific to Cisco FTD."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def send_config_set(self, *args: Any, **kwargs: Any) -> str:
        """Canot change config on FTD via ssh"""
        raise NotImplementedError

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Canot change config on FTD via ssh"""
        return False

    def find_failover(self) -> str:

        command = 'show failover'
        pattern_act = 'This ((C|c)ontext|(H|h)ost): .*Active'
        pattern_stby = 'This ((C|c)ontext|(H|h)ost): .*Standby'
        pattern_off = 'Failover Off'

        output = self.send_command(command)

        if "Failover On" in output:

            if re.search(pattern_act, output):
                return "Active"

            elif re.search(pattern_stby, output):
                return "Standby"

            else:
                raise ValueError("Act/Stby Pattern Error")
                return None

        elif re.search(pattern_off, output):
            return "Off"

        else:
            raise ValueError("Act/Stby Unknown Error")
            return None

