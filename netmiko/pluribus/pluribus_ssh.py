import time
from netmiko.base_connection import BaseConnection


class PluribusSSH(BaseConnection):
    """Common methods for Pluribus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_mode = False

    def disable_paging(self, command="pager off", delay_factor=1):
        """Make sure paging is disabled."""
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def session_preparation(self):
        """Prepare the netmiko session."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, *args, **kwargs):
        """
        Pluribus devices don't have a config mode.
        Therefore it can be considered as always in config mode.
        """
        return self._config_mode

    def config_mode(self, *args, **kwargs):
        """No special actions to enter in config mode."""
        self._config_mode = True
        return ""

    def exit_config_mode(self, *args, **kwargs):
        """No special actions to exit config mode."""
        self._config_mode = False
        return ""
