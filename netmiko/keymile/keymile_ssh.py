import re
import time

from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.cisco.cisco_ios import CiscoIosBase
from netmiko import log


class KeymileSSH(CiscoIosBase):
    def __init__(self, **kwargs):
        kwargs.setdefault("default_enter", "\r\n")
        return super(KeymileSSH, self).__init__(**kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, *args, **kwargs):
        """Keymile doesn't use paging."""
        return ""

    def check_config_mode(self, check_string="", pattern=""):
        """Keymile doesn't use config mode."""
        return False

    def config_mode(self, config_command="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def exit_config_mode(self, exit_config="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def check_enable_mode(self, check_string=""):
        """Keymile doesn't use enable mode."""
        return False

    def enable(self, cmd="", pattern="", re_flags=re.IGNORECASE):
        """Keymile doesn't use enable mode."""
        pass

    def exit_enable_mode(self, exit_command="exit"):
        """Keymile doesn't use enable mode."""
        pass

    def strip_prompt(self, a_string):
        """Remove appending empty line and prompt from output"""
        self._write_session_log(a_string)
        a_string = a_string[:-1]
        return super(KeymileSSH, self).strip_prompt(a_string=a_string)

    def send_command(self, *args, **kwargs):
        """make "cd /path" work"""
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs["command_string"]

        if "cd" in command_string:
            dest = command_string.split(" ", 1)[1]
            self.base_prompt = dest
            kwargs["expect_string"] = dest

        output = super(KeymileSSH, self).send_command(*args, **kwargs)
        return output

    def set_base_prompt(self, pri_prompt_terminator=">"):
        """ set prompt termination  to >"""
        prompt = super(KeymileSSH, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator
        )
        self.base_prompt = prompt
        return self.base_prompt
