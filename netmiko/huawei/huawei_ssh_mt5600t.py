from huawei_ssh import HuaweiSSH

class HuaweiSSH_MT5600T(HuaweiSSH):

    def session_preparation(self):
        """mmi-mode removes STDIN from beeing displayed in shell, it also sets terminal length 0"""
        self.set_base_prompt()
        self.disable_paging(command="mmi-mode enable\n")

    def config_mode(self, config_command='config'):
        """config instead of system-view"""
        return super(HuaweiSSH_MT5600T, self).config_mode(config_command=config_command)

    def check_config_mode(self, check_string=')'):
        """check for ')' instead of ']'"""
        return super(HuaweiSSH_MT5600T, self).check_config_mode(check_string=check_string)

    def set_base_prompt(self, alt_prompt_terminator=')'):
        """check for ')' instead of ']'"""
        super(HuaweiSSH_MT5600T, self).set_base_prompt(alt_prompt_terminator=alt_prompt_terminator)