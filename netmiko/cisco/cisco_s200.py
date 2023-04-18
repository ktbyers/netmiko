import re
from os import path

from paramiko import SSHClient
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import NetmikoAuthenticationException


class CiscoS200Base(CiscoSSHConnection):
    """
    Support for Cisco SG200 series of devices.

    This connection class writes for low cost switches SG200 series, in which there is no command:

    ip ssh password-auth

    Consequently, Netmiko must handle the SSH authentication itself.
    """

    prompt_pattern = r"(?m:[>#]\s*$)"  # force re.Multiline

    def _build_ssh_client(self) -> SSHClient:
        """Allow passwordless authentication for Cisco SG200 devices being provisioned."""

        # Create instance of SSHClient object. Use noauth
        remote_conn_pre = SSHClient_noauth()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Cisco SG2xx presents with the following on login

        login as: user

        Welcome to Layer 2 Managed Switch

        Username: user
        Password:****
        """
        output = ""
        uname = "Username:"
        login = "login as"
        password = "ssword"
        pattern = rf"(?:{uname}|{login}|{password}|{self.prompt_pattern})"

        while True:
            new_data = self.read_until_pattern(pattern=pattern, read_timeout=25.0)
            output += new_data

            # Fully logged-in, switch prompt detected.
            if re.search(self.prompt_pattern, new_data):
                return

            if uname in new_data or login in new_data:
                assert isinstance(self.username, str)
                self.write_channel(self.username + self.RETURN)
            elif password in new_data:
                assert isinstance(self.password, str)
                self.write_channel(self.password + self.RETURN)
            else:
                msg = f"""
Failed to login to Cisco SG2xx.

Pattern not detected: {pattern}
output:

{output}

"""
                raise NetmikoAuthenticationException(msg)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = True,
        confirm_response: str = "Y",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CiscoS200SSH(CiscoS200Base):
    pass


class CiscoS200Telnet(CiscoS200Base):
    pass
