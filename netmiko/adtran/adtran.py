import time
import re
from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log


class AdtranOSBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def strip_ansi_escape_codes(self, string_buffer):
        """
            Even with terminal width set to max, some commands such as
            an EVC map, may start producing \x08 eg:
            interface muxponder-highspeed 1/1/8 ten-gigabit-et\x08\x08\x08

            Adtran uses the backspace to allow more characters to appear
        """
        output = self.strip_backspaces(string_buffer)
        new_output = output.strip()
        log.debug("Stripping ANSI escape codes")
        log.debug(f"new_output = {new_output}")
        return super().strip_ansi_escape_codes(new_output)

    def check_enable_mode(self, check_string="#"):
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="", re_flags=re.IGNORECASE):
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command="disable"):
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=")#"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="config term", pattern=""):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def set_base_prompt(self, pri_prompt_terminator=">", alt_prompt_terminator="#"):
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
        )

class AdtranOSSSH(AdtranOSBase):
    pass
