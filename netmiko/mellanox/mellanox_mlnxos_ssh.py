"""Mellanox MLNX-OS Switch support."""
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log


class MellanoxMlnxosSSH(CiscoSSHConnection):
    """Mellanox MLNX-OS Switch support."""

    def enable(self, cmd="enable", pattern="#", re_flags=re.IGNORECASE):
        """Enter into enable mode."""
        output = ""
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output

    def config_mode(self, config_command="config term", pattern="#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def check_config_mode(self, check_string="(config", pattern=r"#"):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def disable_paging(self, command="no cli session paging enable", delay_factor=1):
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def exit_config_mode(self, exit_config="exit", pattern="#"):
        """Mellanox does not support a single command to completely exit configuration mode.

        Consequently, need to keep checking and sending "exit".
        """
        output = ""
        check_count = 12
        while check_count >= 0:
            if self.check_config_mode():
                self.write_channel(self.normalize_cmd(exit_config))
                output += self.read_until_pattern(pattern=pattern)
            else:
                break
            check_count -= 1

        # One last check for whether we successfully exited config mode
        if self.check_config_mode():
            raise ValueError("Failed to exit configuration mode")

        log.debug(f"exit_config_mode: {output}")
        return output

    def save_config(
        self, cmd="configuration write", confirm=False, confirm_response=""
    ):
        """Save Config on Mellanox devices Enters and Leaves Config Mode"""
        output = self.enable()
        output += self.config_mode()
        output += self.send_command(cmd)
        output += self.exit_config_mode()
        return output
