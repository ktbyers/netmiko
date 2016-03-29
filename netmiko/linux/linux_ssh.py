import re
from netmiko.ssh_connection import SSHConnection


class LinuxSSH(SSHConnection):

    def set_base_prompt(self, pri_prompt_terminator='$',
                        alt_prompt_terminator='#', delay_factor=.1):
        """Determine base prompt."""
        return super(SSHConnection, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

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
        return super(SSHConnection, self).exit_config_mode(exit_config=exit_config)

    def check_enable_mode(self, check_string='#'):
        return self.check_config_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command='exit'):
        return self.exit_config_mode(exit_config=exit_command)

    def enable(self, cmd='sudo su', pattern='ssword', re_flags=re.IGNORECASE):
        """Attempt to become root."""
        return super(SSHConnection, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)
