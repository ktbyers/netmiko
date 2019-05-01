import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class switchosSSH(CiscoSSHConnection):

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self.base_prompt = r"\[.*?\] \>.*\[.*?\] \>"
        # Clear the read buffer
        self.write_channel(self.RETURN)
        self.set_base_prompt()

    def _modify_connection_params(self):
         self.username += "+cetw511"

    def _enter_shell(self):
        """Already in shell."""
        return ""

    def _return_cli(self):
        """The shell is the CLI."""
        return ""

    def disable_paging(self, *args, **kwargs):
        """Microtik does not have paging by default."""
        return ""

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on RouterOS"""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on RouterOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on RouterOS."""
        pass

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
        return super(switchosSSH, self).send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
        )

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        raise NotImplementedError
