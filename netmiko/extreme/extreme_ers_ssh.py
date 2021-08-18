"""Netmiko support for Extreme Ethernet Routing Switch."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection

# Extreme ERS presents Enter Ctrl-Y to begin.
CTRL_Y = "\x19"


class ExtremeErsSSH(CiscoSSHConnection):
    """Netmiko support for Extreme Ethernet Routing Switch."""

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Extreme ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin.
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Handle 'Enter Ctrl-Y to begin'
        output = ""
        i = 0
        while i <= 12:
            output = self.read_channel()
            if output:
                if "Ctrl-Y" in output:
                    self.write_channel(CTRL_Y)
                if "sername" in output:
                    assert isinstance(self.username, str)
                    self.write_channel(self.username + self.RETURN)
                elif "ssword" in output:
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(0.5 * delay_factor)
            else:
                self.write_channel(self.RETURN)
                time.sleep(1 * delay_factor)
            i += 1

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
