import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeFOSSSH(CiscoSSHConnection):
    """Brocade Fabric OS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def check_enable_mode(self, check_string=">"):
        """
        Check if in enable mode. Return boolean.
        """
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="", pattern=""):
        """No Enable Mode"""
        return super().enable(cmd=cmd, pattern=pattern)

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=">"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="", pattern=r")#"):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="", pattern="#"):
        return
