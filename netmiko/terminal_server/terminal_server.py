"""Generic Terminal Server driver."""
from netmiko.base_connection import BaseConnection


class TerminalServer(BaseConnection):
    """Generic Terminal Server driver.

    Allow direct write_channel / read_channel operations without session_preparation causing
    an exception.
    """

    def session_preparation(self):
        """Do nothing here; base_prompt is not set; paging is not disabled."""
        pass
    
    def check_config_mode(self, check_string="", pattern=""):
        """Checks if the device is in configuration mode or not."""
        return True

    def config_mode(self, config_command=""):
        """No config mode for F5 devices."""
        return ""

    def exit_config_mode(self, exit_config=""):
        """No config mode for F5 devices."""
        return ""    


class TerminalServerSSH(TerminalServer):
    """Generic Terminal Server driver SSH."""

    pass


class TerminalServerTelnet(TerminalServer):
    """Generic Terminal Server driver telnet."""

    def telnet_login(self, *args, **kwargs):
        # Disable automatic handling of username and password when using terminal server driver
        pass

    def std_login(self, *args, **kwargs):
        return super().telnet_login(*args, **kwargs)
