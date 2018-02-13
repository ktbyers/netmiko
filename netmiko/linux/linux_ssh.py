from __future__ import unicode_literals

import re
import socket
import time

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoTimeoutException


class LinuxSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        return super(LinuxSSH, self).session_preparation()

    def disable_paging(self, *args, **kwargs):
        """Linux doesn't have paging by default."""
        return ""

    def set_base_prompt(self, pri_prompt_terminator='$',
                        alt_prompt_terminator='#', delay_factor=1):
        """Determine base prompt."""
        return super(LinuxSSH, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """Can't exit from root (if root)"""
        if self.username == "root":
            exit_config_mode = False
        return super(LinuxSSH, self).send_config_set(config_commands=config_commands,
                                                     exit_config_mode=exit_config_mode,
                                                     **kwargs)

    def check_config_mode(self, check_string='#'):
        """Verify root"""
        return self.check_enable_mode(check_string=check_string)

    def config_mode(self, config_command='sudo su'):
        """Attempt to become root."""
        return self.enable(cmd=config_command)

    def exit_config_mode(self, exit_config='exit'):
        return self.exit_enable_mode(exit_command=exit_config)

    def check_enable_mode(self, check_string='#'):
        """Verify root"""
        return super(LinuxSSH, self).check_enable_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command='exit'):
        """Exit enable mode."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            time.sleep(.3 * delay_factor)
            self.set_base_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def enable(self, cmd='sudo su', pattern='ssword', re_flags=re.IGNORECASE):
        """Attempt to become root."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        output = ""
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            time.sleep(.3 * delay_factor)
            try:
                output += self.read_channel()
                if re.search(pattern, output, flags=re_flags):
                    self.write_channel(self.normalize_cmd(self.secret))
                self.set_base_prompt()
            except socket.timeout:
                raise NetMikoTimeoutException("Timed-out reading channel, data not available.")
            if not self.check_enable_mode():
                msg = "Failed to enter enable mode. Please ensure you pass " \
                      "the 'secret' argument to ConnectHandler."
                raise ValueError(msg)
        return output

    def cleanup(self):
        """Try to Gracefully exit the SSH session."""
        self.write_channel("exit" + self.RETURN)

    def save_config(self, cmd='', confirm=True, confirm_response=''):
        """Not Implemented"""
        raise NotImplementedError
