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
        self.set_base_prompt(alt_prompt_terminator="$")

    def check_config_mode1(self, check_string="#", pattern=""):
        log.debug(f"pattern: {pattern}")
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        log.debug(f"check_config_mode: {repr(output)}")
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        log.debug(f"check_config_mode: {repr(output)}")
        return check_string in output

    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """Disable paging sets the command: terminal length 0

        :param command: Device command to disable pagination of output
        :type command: str
        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        return self.send_command(command, expect_string=r"[\#]")

    def config_mode(self, config_command="configure terminal", pattern="#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def _enter_shell(self):
        """Enter the sonic-cli Shell."""
        log.debug(f"Enter sonic-cli Shell.")
        output = self.send_command("sonic-cli", expect_string=r"[\#]")
        self.send_command("terminal length 0", expect_string=r"[\#]")

        return output

    def enable(self, *args, **kwargs):
        raise AttributeError("Dell Sonic switches do not support enable mode!")

    def _return_cli(self):
        """Return to the CLI."""
        return self.send_command("exit", expect_string=r"[\$]")
