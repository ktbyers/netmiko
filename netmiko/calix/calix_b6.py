"""Calix B6 SSH Driver for Netmiko"""
from typing import Any
import time
from os import path

from paramiko import SSHClient

from netmiko.cisco_base_connection import CiscoSSHConnection


class SSHClient_noauth(SSHClient):
    """Set noauth when manually handling SSH authentication."""

    def _auth(self, username: str, *args: Any) -> None:
        self._transport.auth_none(username)  # type: ignore
        return


class CalixB6Base(CiscoSSHConnection):
    """Common methods for Calix B6, both SSH and Telnet."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> Any:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
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
                    assert isinstance(self.username, str)
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 0.5)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1)
            i += 1

    def check_config_mode(self, check_string: str = ")#", pattern: str = "") -> bool:
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string)

    def save_config(
        self,
        cmd: str = "copy run start",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CalixB6SSH(CalixB6Base):
    """Calix B6 SSH Driver.

    To make it work, we have to override the SSHClient _auth method and manually handle
    the username/password.
    """

    def _build_ssh_client(self) -> SSHClient:
        """Prepare for Paramiko SSH connection."""
        # Create instance of SSHClient object
        # If not using SSH keys, we use noauth
        if not self.use_keys:
            remote_conn_pre: SSHClient = SSHClient_noauth()
        else:
            remote_conn_pre = SSHClient()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre


class CalixB6Telnet(CalixB6Base):
    """Calix B6 Telnet Driver."""

    pass
