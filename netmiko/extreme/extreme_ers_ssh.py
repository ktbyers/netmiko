"""Netmiko support for Extreme Ethernet Routing Switch."""
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import NetmikoAuthenticationException

# Extreme ERS presents Enter Ctrl-Y to begin.
CTRL_Y = "\x19"


class ExtremeErsSSH(CiscoSSHConnection):
    """Netmiko support for Extreme Ethernet Routing Switch."""

    prompt_pattern = r"(?m:[>#]\s*$)"  # force re.Multiline

    def session_preparation(self) -> None:
        # special_login_handler() will always ensure self.prompt_pattern
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Extreme ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin

        Older devices the Ctrl-Y is before SSH-login (not 100% sure of this).

        Newer devices this is after SSH-login.
        """

        output = ""
        uname = "sername"
        password = "ssword"
        cntl_y = "Ctrl-Y"
        pattern = rf"(?:{uname}|{password}|{cntl_y}|{self.prompt_pattern})"
        while True:
            new_data = self.read_until_pattern(pattern=pattern, read_timeout=25.0)
            output += new_data
            if re.search(self.prompt_pattern, new_data):
                return

            if cntl_y in new_data:
                self.write_channel(CTRL_Y)
            elif uname in new_data:
                assert isinstance(self.username, str)
                self.write_channel(self.username + self.RETURN)
            elif password in new_data:
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
            else:
                msg = f"""

Failed to login to Extreme ERS Device.

Pattern not detected: {pattern}
output:

{output}

"""
                raise NetmikoAuthenticationException(msg)

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
