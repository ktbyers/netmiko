import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection


class AdtranOSBase(CiscoBaseConnection):
    def __init__(self, *args, **kwargs):
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        return super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string="#"):
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="", re_flags=re.IGNORECASE):
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command="disable"):
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=")#"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="config term", pattern=""):
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def set_base_prompt(
        self, pri_prompt_terminator=">", alt_prompt_terminator="#", **kwargs
    ):
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            **kwargs
        )


class AdtranOSSSH(AdtranOSBase):
    pass
