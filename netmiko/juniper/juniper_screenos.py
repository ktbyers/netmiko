import time
from netmiko.base_connection import BaseConnection
import re


class JuniperScreenOsSSH(BaseConnection):
    """
    Implement methods for interacting with Juniper ScreenOS devices.
    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="set console page 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """
        ScreenOS is adding '(VR-NAME)' after the hostname to the prompt when
        using 'set vr VR-NAME' command.
        The solution is to remove it and trailing '-' from base_prompt
        """
        cur_base_prompt = re.sub(
            r"\(.*\)-$|-$", "", super().set_base_prompt(*args, **kwargs)
        )
        match = re.search(r"(.*)", cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        else:
            print(f"else : {self.base_prompt}")
            return cur_base_prompt

    def send_command(self, *args, **kwargs):
        """ScreenOS needs special handler here due to the prompt changes."""
        # Change send_command behavior to use self.base_prompt
        kwargs.setdefault("auto_find_prompt", False)

        # refresh self.base_prompt
        self.set_base_prompt()
        return super().send_command(*args, **kwargs)

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Juniper ScreenOS."""
        return True

    def enable(self, *args, **kwargs):
        """No enable mode on Juniper ScreenOS."""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Juniper ScreenOS."""
        return ""

    def check_config_mode(self, *args, **kwargs):
        """No configuration mode on Juniper ScreenOS."""
        return False

    def config_mode(self, *args, **kwargs):
        """No configuration mode on Juniper ScreenOS."""
        return ""

    def exit_config_mode(self, *args, **kwargs):
        """No configuration mode on Juniper ScreenOS."""
        return ""

    def save_config(self, cmd="save config", confirm=False, confirm_response=""):
        """Save Config."""
        return self.send_command(command_string=cmd)
