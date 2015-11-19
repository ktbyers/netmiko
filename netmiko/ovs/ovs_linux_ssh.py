from netmiko.ssh_connection import SSHConnection


class OvsLinuxSSH(SSHConnection):


    def check_config_mode(self, check_string='#'):
        return super(SSHConnection, self).check_config_mode(check_string=check_string)


    def set_base_prompt(self, pri_prompt_terminator='$',
                                    alt_prompt_terminator='#', delay_factor=.5):
        return super(SSHConnection, self).set_base_prompt(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                delay_factor=delay_factor)


    def config_mode(self, config_command='sudo su'):
        return super(SSHConnection, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='exit'):
        return super(SSHConnection, self).exit_config_mode(exit_config=exit_config)

    def exit_enable_mode(self, exit_command='exit'):
        pass

    def check_enable_mode(self, check_string='$'):
        pass

    def enable(self):
        pass
