import re
import time

from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer


class EricssonIposSSH(BaseConnection):

    def check_enable_mode(self, check_string="#"):
        """
        Check if in enable mode. Return boolean.
        """
        return super().check_enable_mode(
            check_string=check_string
        )

    def enable(self, cmd="", pattern="ssword", re_flags=re.IGNORECASE):
        """
        Enter enable mode.
        """
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            re_flags=re_flags
        )

    def exit_enable_mode(self, exit_command="disable"):
        """
        Exits enable (privileged exec) mode.
        """
        return super().exit_enable_mode(
            exit_command=exit_command
        )

    
    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string,
            pattern=pattern
        )

    def config_mode(self, config_command="configure", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(
            config_command=config_command,
            pattern=pattern
        )

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """
        Exit from configuration mode.
        Ercisson output :
            end                   Commit configuration changes and return to exec mode
        """
        return super().exit_config_mode(
            exit_config=exit_config,
            pattern=pattern
        )
