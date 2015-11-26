from netmiko.ssh_connection import SSHConnection


class LinuxSSH(SSHConnection):

    def check_config_mode(self, check_string='#'):
        return super(SSHConnection, self).check_config_mode(check_string=check_string)

    def set_base_prompt(self, pri_prompt_terminator='$',
            alt_prompt_terminator='#', delay_factor=.5):
        return super(SSHConnection, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        # Do not exit from config mode for root,
        # it is impossible
        if self.username == "root":
            exit_config_mode=False
        return super(SSHConnection, self).send_config_set(config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs)

    def config_mode(self, config_command='sudo su'):
        output = self.send_command(config_command)
        self.send_command(self.secret)
        return super(SSHConnection, self).config_mode(config_command='')

    def exit_config_mode(self, exit_config='exit'):
        return super(SSHConnection, self).exit_config_mode(exit_config=exit_config)

    def exit_enable_mode(self, exit_command='exit'):
        pass

    def check_enable_mode(self, check_string='#'):
        pass

    def enable(self):
        pass
