"""Extreme support."""
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeExosBase(CiscoSSHConnection):
    """Extreme Exos support.

    Designed for EXOS >= 15.0
    """

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging")
        self.send_command_timing("disable cli prompting")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """
        Extreme attaches an id to the prompt. The id increases with every command.
        It needs to br stripped off to match the prompt. Eg.

            testhost.1 #
            testhost.2 #
            testhost.3 #

        If new config is loaded and not saved yet, a '* ' prefix appears before the
        prompt, eg.

            * testhost.4 #
            * testhost.5 #
        """
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        # Strip off any leading * or whitespace chars; strip off trailing period and digits
        match = re.search(r"[\*\s]*(.*)\.\d+", cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        else:
            return self.base_prompt

    def send_command(self, *args, **kwargs):
        """Extreme needs special handler here due to the prompt changes."""

        # Change send_command behavior to use self.base_prompt
        kwargs.setdefault("auto_find_prompt", False)

        # refresh self.base_prompt
        self.set_base_prompt()
        return super().send_command(*args, **kwargs)

    def config_mode(self, config_command=""):
        """No configuration mode on Extreme Exos."""
        return ""

    def check_config_mode(self, check_string="#"):
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string)

    def exit_config_mode(self, exit_config=""):
        """No configuration mode on Extreme Exos."""
        return ""

    def save_config(
        self, cmd="save configuration primary", confirm=False, confirm_response=""
    ):
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class ExtremeExosSSH(ExtremeExosBase):
    pass


class ExtremeExosTelnet(ExtremeExosBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
