"""Ericsson MiniLink driver."""
import time
from os import path
from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.base_connection import BaseConnection
from netmiko.exceptions import NetmikoTimeoutException


class EricssonMinilinkBase(BaseConnection):
    """Ericsson MiniLink Base class"""

    def __init__(
        self,
        default_ssh_username: str = "cli",
        login_timeout: int = 20,
        login_sleep_time: int = 0.1,
        login_sleep_multiplier: int = 5,
        *args,
        **kwargs,
    ):
        self.login_timeout = login_timeout
        self.login_sleep_time = login_sleep_time
        self.login_sleep_multiplier = login_sleep_multiplier

        # Remove username from kwargs to avoid duplicates
        self.real_username = None
        if "username" in kwargs:
            self.real_username = kwargs["username"]
            kwargs.pop("username")

        super().__init__(username=default_ssh_username, *args, **kwargs)

        # Add back the username
        if self.real_username:
            kwargs["username"] = self.real_username

    def _build_ssh_client(self) -> SSHClient:
        if not self.use_keys:
            remote_conn_pre: SSHClient = SSHClient_noauth()
        else:
            remote_conn_pre: SSHClient()

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

    def special_login_handler(self) -> None:
        """Handle Ericcsons Special MINI-LINK CLI login
        ------------------------------------------
        MINI-LINK <model>  Command Line Interface
        ------------------------------------------

        Welcome to <hostname>
        User:
        Password:
        """
        start = time.time()
        while time.time() - start < self.login_timeout:
            output = self.read_channel()

            # Check if there is any data returned yet
            if not output:
                # Sleep before checking again
                time.sleep(self.login_sleep_time * self.login_sleep_multiplier)
                output = self.read_channel()
                # If still no output, send an <enter> and try again in next loop
                if not output:
                    self.write_channel(self.RETURN)
                    continue

            # Special login handle
            if "login:" in output or "User:" in output:
                self.write_channel(self.real_username + self.RETURN)
            elif "password:" in output or "Password:" in output:
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
                break
            elif "busy" in output:
                self.disconnect()
                raise ValueError("CLI is currently busy")

            # If none of the checks above is a success, sleep and try again
            time.sleep(self.login_sleep_time)

        else:  # no-break
            msg = f"""Login process failed to device. Unable to login in {self.login_timeout} seconds"""
            raise NetmikoTimeoutException(msg)

    def commit():
        pass

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class EricssonMinilink63SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 63XX (SSH)"""

    def check_config_mode(
        self,
        check_string: str = ")#",
    ) -> bool:
        return super().check_config_mode(check_string=check_string)

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = r"[)#]",
    ) -> None:
        """
        Enter Configuration Mode

        This is intended for the ML6600 series traffic node. This driver should work
        with the ML6300 series aswell, but they do not implement a config mode.
        """
        if self.check_config_mode():
            return

        self.write_channel(self.normalize_cmd(config_command))
        self.read_until_pattern(pattern)

        if not self.check_config_mode():
            raise ValueError("Failed to enter configuration mode.")

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "#") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response=""
    ) -> str:
        """Save Config for Ericsson Minilink"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def commit(self):
        if self.check_config_mode():
            self.exit_config_mode()

        output = self.save_config()
        self.exit_config_mode()
        return output


class EricssonMinilink66SSH(EricssonMinilinkBase):
    """Common Methods for Ericsson Minilink 66XX (SSH)"""

    def check_config_mode(
        self,
        check_string: str = ")#",
    ) -> bool:
        return super().check_config_mode(check_string=check_string)

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = r"[)#]",
    ) -> None:
        """
        Enter Configuration Mode

        This is intended for the ML6600 series traffic node. This driver should work
        with the ML6300 series aswell, but they do not implement a config mode.
        """
        if self.check_config_mode():
            return

        self.write_channel(self.normalize_cmd(config_command))
        self.read_until_pattern(pattern)

        if not self.check_config_mode():
            raise ValueError("Failed to enter configuration mode.")

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "#") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response=""
    ) -> str:
        """Save Config for Ericsson Minilink"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def commit(self):
        if self.check_config_mode():
            self.exit_config_mode()

        output = self.save_config()
        self.exit_config_mode()
        return output
