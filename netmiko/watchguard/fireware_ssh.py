import time
from netmiko.base_connection import BaseConnection


class WatchguardFirewareSSH(BaseConnection):
    """
    Implements methods for communicating with Watchguard Firebox firewalls.
    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('#').
        """
        self._test_channel_read()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=")#", pattern="#"):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(self, config_command="configure", pattern="#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="exit", pattern="#"):
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, *args, **kwargs):
        """No save config on Watchguard."""
        pass
