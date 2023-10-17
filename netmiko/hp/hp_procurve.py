import re
import time
import socket
from os import path
from typing import Optional, Any

from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log
from netmiko.exceptions import ReadTimeout


class HPProcurveBase(CiscoSSHConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ProCurve's seem to fail more on connection than they should?
        # increase conn_timeout to try to improve this.
        conn_timeout = kwargs.get("conn_timeout")
        kwargs["conn_timeout"] = 20 if conn_timeout is None else conn_timeout

        disabled_algorithms = kwargs.get("disabled_algorithms")
        if disabled_algorithms is None:
            disabled_algorithms = {"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}
            kwargs["disabled_algorithms"] = disabled_algorithms

        super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        """
        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        # ProCurve has an odd behavior where the router prompt can show up
        # before the 'Press any key to continue' message. Read up until the
        # Copyright banner to get past this.
        try:
            self.read_until_pattern(pattern=r".*opyright", read_timeout=1.3)
        except ReadTimeout:
            pass

        # Procurve uses 'Press any key to continue'
        try:
            data = self.read_until_pattern(
                pattern=r"(any key to continue|[>#])", read_timeout=3.0
            )
            if "any key to continue" in data:
                self.write_channel(self.RETURN)
                self.read_until_pattern(pattern=r"[>#]", read_timeout=3.0)
        except ReadTimeout:
            pass

        self.set_base_prompt()
        # If prompt still looks odd, try one more time
        if len(self.base_prompt) >= 25:
            self.set_base_prompt()

        # ProCurve requires elevated privileges to disable output paging :-(
        self.enable()
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        command = "no page"
        self.disable_paging(command=command)

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        The pattern is needed as it is not in the parent class.

        Not having this will make each check_config_mode() call take ~2 seconds.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "password",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
        default_username: str = "",
    ) -> str:
        """Enter enable mode"""

        if check_state and self.check_enable_mode():
            return ""

        if not default_username:
            default_username = self.username

        output = ""
        username_pattern = r"(username|login|user name)"
        pwd_pattern = pattern
        prompt_pattern = r"[>#]"
        full_pattern = rf"(username|login|user name|{pwd_pattern}|{prompt_pattern})"

        # Send the enable command
        self.write_channel(cmd + self.RETURN)
        new_output = self.read_until_pattern(
            full_pattern, read_timeout=15, re_flags=re_flags
        )

        # Send the username
        if re.search(username_pattern, new_output, flags=re_flags):
            output += new_output
            self.write_channel(default_username + self.RETURN)
            full_pattern = rf"({pwd_pattern}|{prompt_pattern})"
            new_output = self.read_until_pattern(
                full_pattern, read_timeout=15, re_flags=re_flags
            )

        # Send the password
        if re.search(pwd_pattern, new_output, flags=re_flags):
            output += new_output
            self.write_channel(self.secret + self.RETURN)
            new_output = self.read_until_pattern(
                prompt_pattern, read_timeout=15, re_flags=re_flags
            )

        output += new_output
        log.debug(f"{output}")
        self.clear_buffer()
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        if not self.check_enable_mode():
            raise ValueError(msg)
        return output

    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""

        # Exit configuration mode.
        try:
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass

        # Terminate SSH/telnet session
        self.write_channel(command + self.RETURN)

        output = ""
        for _ in range(10):

            # The connection might be dead here.
            try:
                # "Do you want to log out"
                # "Do you want to save the current"
                pattern = r"Do you want.*"
                new_output = self.read_until_pattern(pattern, read_timeout=1.5)
                output += new_output

                if "Do you want to log out" in new_output:
                    self.write_channel("y" + self.RETURN)
                    break
                elif "Do you want to save the current" in new_output:
                    # Don't automatically save the config (user's responsibility)
                    self.write_channel("n" + self.RETURN)
            except socket.error:
                break
            except ReadTimeout:
                break
            except Exception:
                break

            time.sleep(0.05)

        # Set outside of loop
        self._session_log_fin = True

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class HPProcurveSSH(HPProcurveBase):
    def _build_ssh_client(self) -> SSHClient:
        """Allow passwordless authentication for HP devices being provisioned."""

        # Create instance of SSHClient object. If no SSH keys and no password, then use noauth
        remote_conn_pre: SSHClient
        if not self.use_keys and not self.password:
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


class HPProcurveTelnet(HPProcurveBase):
    def telnet_login(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        username_pattern: str = r"(Login Name:|sername:)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 60,
    ) -> str:
        """Telnet login: can be username/password or just password."""
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
