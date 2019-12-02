import time
from netmiko.base_connection import BaseConnection


class JuniperScreenOsBase(BaseConnection):
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

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Juniper ScreenOS."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Juniper ScreenOS."""
        pass

    def check_config_mode(self, check_string=""):
        """Checks whether in configuration mode. Returns a boolean."""
        return self._in_config_mode

    def save_config(self, cmd="save config", confirm=False, confirm_response=""):
        """Save Config."""
        return self.send_command(command_string=cmd)

    def config_mode(self):
        """No configuration mode on Juniper ScreenOS."""
        self._in_config_mode = True
        return ""

    def exit_config_mode(self, exit_config="-"):
        """No configuration mode on Juniper ScreenOS."""
        self._in_config_mode = False
        return ""


class JuniperScreenOsSSH(JuniperScreenOsBase):
    pass
