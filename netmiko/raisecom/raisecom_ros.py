from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_auth import SSHClient_noauth
import re
import time
from socket import socket
from paramiko import SSHClient

from netmiko._telnetlib.telnetlib import (
    IAC,
    DO,
    DONT,
    WILL,
    WONT,
    SB,
    SE,
    ECHO,
    SGA,
    NAWS,
)
from netmiko.exceptions import NetmikoAuthenticationException


class RaisecomRosBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging("terminal page-break disable")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def _get_ssh_client_instance(self) -> SSHClient:
        """If not using SSH keys or agent, use noauth."""
        if not self.use_keys and not self.allow_agent:
            return SSHClient_noauth()
        return SSHClient()

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config."""
        self.exit_config_mode()
        self.enable()
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)


class RaisecomRosSSH(RaisecomRosBase):
    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Raisecom presents with the following on login (in certain OS versions)
        Login: user
        Password:****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "Login:" in output:
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    assert self.password is not None
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1


class RaisecomRosTelnet(RaisecomRosBase):
    @staticmethod
    def _process_option(telnet_sock: socket, cmd: bytes, opt: bytes) -> None:
        """
        enable ECHO, SGA, set window size to [500, 50]
        """
        if cmd == WILL:
            if opt in [ECHO, SGA]:
                # reply DO ECHO / DO SGA
                telnet_sock.sendall(IAC + DO + opt)
            else:
                telnet_sock.sendall(IAC + DONT + opt)
        elif cmd == DO:
            if opt == NAWS:
                # negotiate about window size
                telnet_sock.sendall(IAC + WILL + opt)
                # Width:500, Weight:50
                telnet_sock.sendall(IAC + SB + NAWS + b"\x01\xf4\x00\x32" + IAC + SE)
            else:
                telnet_sock.sendall(IAC + WONT + opt)

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"(Login|Username)",
        pwd_pattern: str = r"Password",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:

        # set callback function to handle telnet options.
        self.remote_conn.set_option_negotiation_callback(self._process_option)  # type: ignore
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output, flags=re.I):
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output, flags=re.I):
                    assert self.password is not None
                    self.write_channel(self.password + self.TELNET_RETURN)
                    time.sleep(0.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                        alt_prompt_terminator, output, flags=re.M
                    ):
                        return return_msg

                # Check if proper data received
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                    alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                time.sleep(0.5 * delay_factor)
                i += 1
            except EOFError:
                if self.remote_conn is not None:
                    self.remote_conn.close()
                msg = f"Login failed: {self.host}"
                raise NetmikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        msg = f"Login failed: {self.host}"
        if self.remote_conn is not None:
            self.remote_conn.close()
        raise NetmikoAuthenticationException(msg)
