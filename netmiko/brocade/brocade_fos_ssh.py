import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeFOSSSH(CiscoSSHConnection):
    """Brocade Fabric OS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string=">"):
        """No enable mode. Always return True."""
        return True

    def enable(self, cmd="", pattern="", enable_pattern=None, re_flags=re.IGNORECASE):
        """No Enable Mode."""
        return ""

    def exit_enable_mode(self, exit_command=""):
        """No Enable Mode."""
        return ""

    def check_config_mode(self, check_string="", pattern=""):
        return True

    def config_mode(self, config_command="", pattern="", re_flags=0):
        """No config mode."""
        return ""

    def exit_config_mode(self, exit_config="", pattern="#"):
        return ""
