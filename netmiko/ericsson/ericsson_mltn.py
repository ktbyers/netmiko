"""Ericsson MiniLink driver."""
import time
from os import path
from typing import Any
from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.base_connection import BaseConnection
from netmiko.exceptions import NetmikoTimeoutException


class EricssonMinilinkBase(BaseConnection):
    """Ericsson MiniLink Base class"""

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Remove username from kwargs to avoid duplicates
        self._real_username = ""
        if "username" in kwargs:
            # Saving the username for the acutal login prompt
            self._real_username = kwargs["username"]
            # Setting CLI as the default ssh username
            kwargs["username"] = "cli"

        super().__init__(*args, **kwargs)

        # Add back the username
        if self._real_username:
            kwargs["username"] = self._real_username

    def _build_ssh_client(self) -> SSHClient:
        remote_conn_pre: SSHClient
        if not self.use_keys:
            remote_conn_pre = SSHClient_noauth()
        else:
            remote_conn_pre = SSHClient()

        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre

    def session_preparation(self) -> None:
        self.set_base_prompt(
            pri_prompt_terminator="#", alt_prompt_terminator=">", delay_factor=1
        )

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Handle Ericcsons Special MINI-LINK CLI login
        ------------------------------------------
        MINI-LINK <model>  Command Line Interface
        ------------------------------------------

        Welcome to <hostname>
        User:
        Password:
        """
        if not self.auth_timeout:
            self.auth_timeout = 20
        # We are using sleep here due to Ericsson MLTN being slow on login
        start = time.time()
        output = ""
        while time.time() - start < self.auth_timeout:
            output += self.read_channel()

            # Check if there is any data returned yet
            if not output:
                # Sleep before checking again
                time.sleep(0.5)
                output += self.read_channel()
                # If still no output, send an <enter> and try again in next loop
                if not output:
                    self.write_channel(self.RETURN)
                    continue

            # Special login handle
            if "login:" in output or "User:" in output:
                self.write_channel(self._real_username + self.RETURN)
                # Resetting output since the next will be password
                output = ""
            elif "password:" in output or "Password:" in output:
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
                break
            elif "busy" in output:
                self.disconnect()
                raise ValueError("CLI is currently busy")

            # If none of the checks above is a success, sleep and try again
            time.sleep(1)

        else:  # no-break
            msg = f"""Login process failed to device:
Timeout reached (auth_timeout={self.auth_timeout} seconds)"""
            raise NetmikoTimeoutException(msg)

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config."""
        if self.check_config_mode():
            self.exit_config_mode()

        self.send_command(command_string=cmd, strip_prompt=False, strip_command=False)
        return "success"

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = r"\(config\)#",
        *args,
        **kwargs,
    ) -> str:
        return super().config_mode(config_command, pattern, *args, **kwargs)

    def check_config_mode(
        self, check_string: str = "(config)#", *args, **kwargs
    ) -> bool:
        return super().check_config_mode(check_string, *args, **kwargs)

    def exit_config_mode(self, exit_config: str = "exit", *args, **kwargs) -> str:
        return super().exit_config_mode(exit_config, *args, **kwargs)


class EricssonMinilink63SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 63XX (SSH)"""

    def cleanup(self, command: str = "quit") -> None:
        """Gracefully exit the SSH session."""
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class EricssonMinilink66SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 66XX (SSH)"""

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)
