"""Mellanox MLNX-OS Switch support."""
from __future__ import unicode_literals
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


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
        return super(MellanoxMlnxosSSH, self).config_mode(
            config_command=config_command, pattern=pattern
        )

    def check_config_mode(self, check_string="(config", pattern=r"#"):
        return super(MellanoxMlnxosSSH, self).check_config_mode(
            check_string=check_string, pattern=pattern
        )

    def disable_paging(self, command="terminal length 999", delay_factor=1):
        return super(MellanoxMlnxosSSH, self).disable_paging(
            command=command, delay_factor=delay_factor
        )

    def exit_config_mode(self, exit_config="exit", pattern="#"):
        return super(MellanoxMlnxosSSH, self).exit_config_mode(
            exit_config=exit_config, pattern=pattern
        )

    def save_config(
        self, cmd="configuration write", confirm=False, confirm_response=""
    ):
        """Save Config on Mellanox devices Enters and Leaves Config Mode"""
        output = self.enable()
        output += self.config_mode()
        output += self.send_command(cmd)
        output += self.exit_config_mode()
        return output
