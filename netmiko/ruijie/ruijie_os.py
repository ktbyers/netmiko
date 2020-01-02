"""Ruijie RGOS Support"""
from netmiko.cisco_base_connection import CiscoBaseConnection
import time


class RuijieOSBase(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        """Ruijie OS requires enable mode to set terminal width"""
        self.enable()
        self.disable_paging(command="terminal length 0")
        self.set_terminal_width(command="terminal width 256")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def special_login_handler(self, delay_factor=1):
        """
        Username: ****
        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "username:" in output.lower():
                    self.write_channel(self.username + self.RETURN)
                elif "password:" in output.lower():
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1

    def save_config(self, cmd="write", confirm=False, confirm_response=""):
        """Save config: write"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class RuijieOSSSH(RuijieOSBase):

    pass


class RuijieOSTelnet(RuijieOSBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
