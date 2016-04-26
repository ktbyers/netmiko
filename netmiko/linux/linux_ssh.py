import re
import socket

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_connection import SSHConnection


class LinuxSSH(SSHConnection):

    def set_base_prompt(self, pri_prompt_terminator='$',
                        alt_prompt_terminator='#', delay_factor=.1):
        """Determine base prompt."""
        self.base_prompt = '@'

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """Can't exit from root (if root)"""
        if self.username == "root":
            exit_config_mode = False
        return super(SSHConnection, self).send_config_set(config_commands=config_commands,
                                                          exit_config_mode=exit_config_mode,
                                                          **kwargs)

    def check_config_mode(self, check_string='#'):
        """Verify root"""
        return super(SSHConnection, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='sudo su'):
        """Attempt to become root."""
        return self.enable(cmd=config_command)

    def exit_config_mode(self, exit_config='exit'):
        output = ""
        if self.check_enable_mode():
            self.remote_conn.sendall(self.normalize_cmd(exit_config))
            self.set_base_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_enable_mode(self, check_string='#'):
        return self.check_config_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command='exit'):
        """Exit enable mode."""
        return self.exit_config_mode(exit_config=exit_command)

    def enable(self, cmd='sudo su', pattern='ssword', re_flags=re.IGNORECASE):
        """Attempt to become root."""
        output = ""
        if not self.check_enable_mode():
            self.remote_conn.sendall(self.normalize_cmd(cmd))
            pattern = re.escape(pattern)
            base_prompt_pattern = re.escape(self.base_prompt)
            output=''
            try:
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if re.search(pattern, output, flags=re_flags):
                    self.remote_conn.sendall(self.normalize_cmd(self.secret))
                self.set_base_prompt()
            except socket.timeout:
                raise NetMikoTimeoutException("Timed-out reading channel, data not available.")
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output
