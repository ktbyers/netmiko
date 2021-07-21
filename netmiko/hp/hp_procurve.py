import re
import time
import socket
from os import path
from typing import Any, Optional

from paramiko import SSHClient
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log


class SSHClient_noauth(SSHClient):
    """Set noauth when manually handling SSH authentication."""

    def _auth(self, username: str, *args: Any) -> None:
        transport = self.get_transport()
        assert transport is not None
        transport.auth_none(username)
        return


class HPProcurveBase(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        """
        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        command = self.RETURN + "no page"
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        self.disable_paging(command=command)
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "password",
        enable_pattern: Optional[str] = None,
        re_flags: int = re.IGNORECASE,
        default_username: str = "manager",
    ) -> str:
        """Enter enable mode"""
        delay_factor = self.select_delay_factor(delay_factor=0)
        if self.check_enable_mode():
            return ""

        output = ""
        i = 1
        max_attempts = 5
        while i <= max_attempts:
            self.write_channel(cmd + self.RETURN)
            time.sleep(0.3 * delay_factor)
            new_output = self.read_channel()
            username_pattern = r"(username|login|user name)"
            if re.search(username_pattern, new_output, flags=re_flags):
                output += new_output
                new_output = self._send_command_timing_str(default_username)
            if re.search(pattern, new_output, flags=re_flags):
                output += new_output
                self.write_channel(self.normalize_cmd(self.secret))
                new_output = self.read_channel_timing()
                if self.check_enable_mode():
                    output += new_output
                    return output
            output += new_output
            i += 1

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
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass

        # Terminate SSH/telnet session
        self.write_channel(command + self.RETURN)
        count = 0
        output = ""
        while count <= 5:
            time.sleep(0.5)

            # The connection might be dead here.
            try:
                new_output = self.read_channel()
                output += new_output
            except socket.error:
                break

            if "Do you want to log out" in new_output:
                self.write_channel("y" + self.RETURN)
                time.sleep(0.5)
                output += self.read_channel()

            # Don't automatically save the config (user's responsibility)
            if "Do you want to save the current" in output:
                self.write_channel("n" + self.RETURN)

            try:
                self.write_channel(self.RETURN)
            except socket.error:
                break
            count += 1

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
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        """
        # Procurve over SHH uses 'Press any key to continue'
        delay_factor = self.select_delay_factor(delay_factor=0)
        output = ""
        count = 1
        while count <= 30:
            output += self.read_channel()
            if "any key to continue" in output:
                self.write_channel(self.RETURN)
                break
            else:
                time.sleep(0.33 * delay_factor)
            count += 1

        # Try one last time to past "Press any key to continue
        self.write_channel(self.RETURN)

        super().session_preparation()

    def _build_ssh_client(self) -> SSHClient:
        """Allow passwordless authentication for HP devices being provisioned."""

        # Create instance of SSHClient object. If no SSH keys and no password, then use noauth
        remote_conn_pre = (
            SSHClient_noauth()
            if not self.use_keys and not self.password
            else SSHClient()
        )

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
        username_pattern: str = r"Login Name:",
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
