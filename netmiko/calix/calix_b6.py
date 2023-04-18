"""Calix B6 SSH Driver for Netmiko"""
from typing import Any
import time
from os import path

from paramiko import SSHClient

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.exceptions import NetmikoTimeoutException


class CalixB6Base(CiscoSSHConnection):
    """Common methods for Calix B6, both SSH and Telnet."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def session_preparation(self) -> Any:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        self.disable_paging()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Calix B6 presents with the following on login:

        login as:
        Password: ****
        """
        new_data = ""
        time.sleep(0.1)
        start = time.time()
        login_timeout = 20
        while time.time() - start < login_timeout:
            output = self.read_channel() if not new_data else new_data
            new_data = ""
            if output:
                if "login as:" in output:
                    assert isinstance(self.username, str)
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(0.1)
            else:
                # No new data...sleep longer
                time.sleep(0.5)
                new_data = self.read_channel()
                # If still no data, send an <enter>
                if not new_data:
                    self.write_channel(self.RETURN)
        else:  # no-break
            msg = """
Login process failed to Calix B6 device. Unable to login in {login_timeout} seconds.
"""
            raise NetmikoTimeoutException(msg)

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "", force_regex: bool = False
    ) -> bool:
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
