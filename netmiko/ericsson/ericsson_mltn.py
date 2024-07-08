"""Ericsson MiniLink driver."""

import time
import re
from os import path
from typing import Any
from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.base_connection import BaseConnection
from netmiko.exceptions import NetmikoTimeoutException
from netmiko.no_enable import NoEnable


class EricssonMinilinkBase(NoEnable, BaseConnection):
    """Ericsson MiniLink Base class"""

    prompt_pattern = r"[>#]"

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        # Set default auth_timeout
        if kwargs.get("auth_timeout") is None:
            kwargs["auth_timeout"] = 20

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
        self._test_channel_read(pattern=self.prompt_pattern)
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

        start = time.time()
        output = ""
        assert self.auth_timeout is not None
        while time.time() - start < self.auth_timeout:
            username_pattern = r"(?:login:|User:)"
            password_pattern = "ssword"
            busy = "busy"
            combined_pattern = rf"(?:{username_pattern}|{password_pattern}|{busy})"

            new_output = self.read_until_pattern(
                pattern=combined_pattern, read_timeout=self.auth_timeout
            )
            output += new_output
            if re.search(username_pattern, new_output):
                self.write_channel(self._real_username + self.RETURN)
                continue
            elif re.search(password_pattern, new_output):
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
                break
            elif re.search(busy, new_output):
                self.disconnect()
                raise ValueError("CLI is currently busy")
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
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(config_command, pattern, re_flags=re_flags)

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(check_string, pattern, force_regex=force_regex)

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        return super().exit_config_mode(exit_config, pattern)

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        if self.session_log:
            self.session_log.fin = True
        self.write_channel(command + self.RETURN)


class EricssonMinilink63SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 63XX (SSH)"""

    def cleanup(self, command: str = "quit") -> None:
        """Gracefully exit the SSH session."""
        return super().cleanup(command)


class EricssonMinilink66SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 66XX (SSH)"""

    pass
