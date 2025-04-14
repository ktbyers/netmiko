"""Fiberstore FSOS Driver."""

from typing import Optional, Any
from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.no_enable import NoEnable
import time
from os import path
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException


class FiberstoreFsosSSH(NoEnable, CiscoBaseConnection):
    """
    Fiberstore FSOS uses a non-standard SSH login mechanism. Consequently,
    to make the login work, we have to override the SSHClient _auth method.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        output = self._test_channel_read()
        if "% Authentication Failed" in output:
            assert self.remote_conn is not None
            self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)

        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _build_ssh_client(self) -> SSHClient:
        """Allows you to bypass standard SSH auth while still supporting SSH keys."""

        # If user does not provide SSH key, we use noauth
        remote_conn_pre: SSHClient
        if not self.use_keys:
            remote_conn_pre = SSHClient_noauth()
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

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Fiberstore S3200 presents with the following on login
        Username:
        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        output = ""
        while i <= 12:
            i += 1
            time.sleep(delay_factor)
            output = self.read_channel()
            if output:
                if "Username:" in output:
                    assert self.username is not None
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    assert self.password is not None
                    self.write_channel(self.password + self.RETURN)
                    return


class FiberstoreFsosV2Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        """FS OS requires enable mode to set terminal width"""
        self.enable()
        self.set_terminal_width(command="terminal width 256", pattern="terminal")
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save config: write"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def check_config_mode(
        self,
        check_string: str = "config#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#.*") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)


class FiberstoreFsosV2SSH(FiberstoreFsosV2Base):
    pass


class FiberstoreFsosV2Telnet(FiberstoreFsosV2Base):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
