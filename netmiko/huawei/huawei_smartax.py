import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log


class HuaweiSmartAXSSH(CiscoBaseConnection):
    """Supports Huawei SmartAX and OLT."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self._disable_smart_interaction()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def strip_ansi_escape_codes(self, string_buffer):
        """
        Huawei does a strange thing where they add a space and then add ESC[1D
        to move the cursor to the left one.
        The extra space is problematic.
        """
        code_cursor_left = chr(27) + r"\[\d+D"
        output = string_buffer
        pattern = rf" {code_cursor_left}"
        output = re.sub(pattern, "", output)

        log.debug("Stripping ANSI escape codes")
        log.debug(f"new_output = {output}")
        log.debug(f"repr = {repr(output)}")
        return super().strip_ansi_escape_codes(output)

    def _disable_smart_interaction(self, command="undo smart", delay_factor=1):
        """Disables the { <cr> } prompt to avoid having to sent a 2nd return after each command"""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("In disable_smart_interaction")
        log.debug(f"Command: {command}")
        self.write_channel(command)
        if self.global_cmd_verify is not False:
            output = self.read_until_pattern(pattern=re.escape(command.strip()))
        else:
            output = self.read_until_prompt()
        log.debug(f"{output}")
        log.debug("Exiting disable_smart_interaction")

    def disable_paging(self, command="scroll", **kwargs):
        return super().disable_paging(command=command, **kwargs)

    def config_mode(self, config_command="config", pattern=""):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def check_config_mode(self, check_string=")#"):
        return super().check_config_mode(check_string=check_string)

    def exit_config_mode(self, exit_config="return"):
        return super().exit_config_mode(exit_config=exit_config)

    def check_enable_mode(self, check_string="#"):
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="", re_flags=re.IGNORECASE):
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def set_base_prompt(self, pri_prompt_terminator=">", alt_prompt_terminator="#"):
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
        )

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """ Save Config for HuaweiSSH"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
