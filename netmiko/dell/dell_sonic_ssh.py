"""Netimko driver for Dell EMC PowerSwitch platforms running Dell EMC Open Networking Powered by SONiC"""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log

class DellSonicSSH(CiscoSSHConnection):
    """driver for Dell EMC PowerSwitch platforms running Dell EMC Open Networking Powered by SONiC"""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>$#]")                
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
        self._enter_shell()
        self.disable_paging()
        self.set_base_prompt(alt_prompt_terminator="$")

    #def disable_paging(self, command="terminal length 0", delay_factor=1):
    #    return self.send_command(command, expect_string=r"[\#]")

    def config_mode(self, config_command="configure terminal", pattern="#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def _enter_shell(self):
        """Enter the sonic-cli Shell."""
        log.debug(f"Enter sonic-cli Shell.")
        output = self.send_command("sonic-cli", expect_string=r"[\#]")
        return output

    def enable(self, *args, **kwargs):
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        return ""

    def check_enable_mode(self, *args, **kwargs):
        return True

    def _return_cli(self):
        """Return to the CLI."""
        return self.send_command("exit", expect_string=r"[\$]")
