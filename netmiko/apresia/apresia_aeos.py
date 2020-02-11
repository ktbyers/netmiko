import time
from netmiko.cisco_base_connection import CiscoSSHConnection
import re
from netmiko import log 


class ApresiaAeosBase(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        # before executing "show run", check if it's possible.
        if self.has_privilege():
            self.disable_paging()
        else:
            log.info("This user is non-previleged.")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def has_privilege(self):
        output = self.send_command("show username | include adpro")
        escape_username = re.escape(self.username)
        return re.search(fr"^\s*{escape_username}\s+adpro\s*$", output, re.MULTILINE) is not None

    def disable_paging(self, command="", delay_factor=1):
        self.enable()
        check_command = "show running-config | include terminal length 0"
        output = self.send_command(check_command)

        if self.allow_auto_change and "terminal length 0" not in output:
            self.send_config_set("terminal length 0")
        self.exit_enable_mode()


class ApresiaAeosSSH(ApresiaAeosBase):
    pass


class ApresiaAeosTelnet(ApresiaAeosBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
