"""Calix B6 SSH Driver for Netmiko"""
import time

from netmiko.channel import SSHChannel
from netmiko.cisco_base_connection import CiscoSSHConnection


class CalixB6Channel(SSHChannel):
    def _build_ssh_client(self, no_auth=True):
        """Allow passwordless authentication for HP devices being provisioned."""
        if not self.use_keys:
            super._build_ssh_client(no_auth=no_auth)
        else:
            super._build_ssh_client(no_auth=False)


class CalixB6Base(CiscoSSHConnection):
    """Common methods for Calix B6, both SSH and Telnet."""

    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def special_login_handler(self, delay_factor=1):
        """
        Calix B6 presents with the following on login:

        login as:
        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.25)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "login as:" in output:
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 0.5)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1)
            i += 1

    def check_config_mode(self, check_string=")#", pattern=""):
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string)

    def save_config(self, cmd="copy run start", confirm=False, confirm_response=""):
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CalixB6SSH(CalixB6Base):
    """Calix B6 SSH Driver.

    To make it work, we have to override the SSHClient _auth method and manually handle
    the username/password.
    """

    def _open(self, channel_class=CalixB6Channel):
        """Override channel object creation."""

        super()._open(channel_class=channel_class)


class CalixB6Telnet(CalixB6Base):
    """Calix B6 Telnet Driver."""

    pass
