import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class routerosSSH(CiscoSSHConnection):
    """MicroTik RouterOS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = '\r\n'
        return super(routerosSSH, self).__init__(**kwargs) 

    def session_preparation(self, *args, **kwargs):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
#        self.base_prompt = r"\[.*?\] \>"
        self.base_prompt = r"\[.*?\] \>.*\[.*?\]\s\>\s"
        # Clear the read buffer
        self.write_channel(self.RETURN)
        self.set_base_prompt()

    def _modify_connection_params(self):
         self.username += "+cetw511h4098"

    def _enter_shell(self):
        """Already in shell."""
        return ""

    def _return_cli(self):
        """The shell is the CLI."""
        return ""

    def disable_paging(self):
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

    def save_config(self, *args, **kwargs):
        """No save command, all configuration is atomic"""
        pass
