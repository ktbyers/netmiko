"""
Dell EMC PowerSwitch platforms running Enterprise SONiC Distribution by Dell Technologies Driver
- supports dellenterprisesonic.
"""

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer
from netmiko import log
import time


class DellSonicSSH(CiscoSSHConnection):
    """
    Dell EMC PowerSwitch platforms running Enterprise SONiC Distribution
    by Dell Technologies Driver - supports dellenterprisesonic.
    """

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>$#]")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
        self._enter_shell()
        self.disable_paging()
        self.set_base_prompt(alt_prompt_terminator="$")

    def config_mode(self, config_command="configure terminal", pattern="#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def _enter_shell(self):
        """Enter the sonic-cli Shell."""
        log.debug(f"Enter sonic-cli Shell.")
        output = self.send_command("sonic-cli", expect_string=r"\#")
        return output

    def enable(self, *args, **kwargs):
        """No enable mode on Enterprise SONiC."""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Enterprise SONiC."""
        return ""

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Enterprise SONiC."""
        return True

    def _return_cli(self):
        """Return to the CLI."""
        return self.send_command("exit", expect_string=r"\$")
