"""Ruijie RGOS Support"""
from __future__ import unicode_literals
from __future__ import print_function

from netmiko.cisco_base_connection import CiscoBaseConnection
import time
import re


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

    def enable(self, cmd="enable", pattern="password", re_flags=re.IGNORECASE):
        """Enter enable mode.
        Ruijie>en
        Password:
        Ruijie#
        """
        if self.check_enable_mode():
            return ""
        output = self.send_command_timing(cmd)
        if "password" in output.lower():
            output += self.send_command_timing(self.secret)
        self.clear_buffer()
        return output

    def check_enable_mode(self, check_string="#"):
        return super(RuijieOSBase, self).check_enable_mode(check_string=check_string)

    def config_mode(self, config_command="config"):
        """Enter into config_mode."""
        return super(RuijieOSBase, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="exit"):
        """Exit config_mode."""
        return super(RuijieOSBase, self).exit_config_mode(exit_config=exit_config)

    def check_config_mode(self, check_string="(config)#"):
        """Checks if the device is in configuration mode"""
        return super(RuijieOSBase, self).check_config_mode(check_string=check_string)

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

    def send_config_set(
        self,
        config_commands=None,
        exit_config_mode=False,
        delay_factor=1,
        max_loops=150,
        strip_prompt=False,
        strip_command=False,
        config_mode_command=None,
    ):
        """Remain in configuration mode."""
        return super(RuijieOSBase, self).send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
        )

    def save_config(self, cmd="write", confirm=False):
        """Save config: write"""
        return super(RuijieOSBase, self).save_config(cmd=cmd, confirm=confirm)


class RuijieOSSSH(RuijieOSBase):

    pass


class RuijieOSTelnet(RuijieOSBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super(RuijieOSBase, self).__init__(*args, **kwargs)
