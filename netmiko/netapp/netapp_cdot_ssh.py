from netmiko.base_connection import BaseConnection


class NetAppcDotSSH(BaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        cmd = self.RETURN + "rows 0" + self.RETURN
        self.disable_paging(command=cmd)

    def send_command_with_y(self, *args, **kwargs):
        output = self.send_command_timing(*args, **kwargs)
        if "{y|n}" in output:
            output += self.send_command_timing(
                "y", strip_prompt=False, strip_command=False
            )
        return output

    def check_config_mode(self, check_string="*>"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(
        self, config_command="set -privilege diagnostic -confirmations off"
    ):
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="set -privilege admin -confirmations off"):
        return super().exit_config_mode(exit_config=exit_config)

    def enable(self, *args, **kwargs):
        """No enable mode on NetApp."""
        pass

    def check_enable_mode(self, *args, **kwargs):
        pass

    def exit_enable_mode(self, *args, **kwargs):
        pass
