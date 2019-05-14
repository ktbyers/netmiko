import re
import time

from netmiko.cisco.cisco_ios import CiscoIosBase


class KeymileNOSSSH(CiscoIosBase):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        self.disable_paging()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def config_mode(self, config_command="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def exit_config_mode(self, exit_config="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def check_enable_mode(self, check_string="#"):
        return super(KeymileNOSSSH, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable"):
        return super(KeymileNOSSSH, self).enable(cmd=cmd)

    def exit_enable_mode(self, exit_command="exit"):
        return super(KeymileNOSSSH, self).exit_enable_mode(exit_command=exit_command)
