from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from socket import socket

from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, ECHO, SGA, NAWS, Telnet
from netmiko.exceptions import NetmikoAuthenticationException


class RaisecomRoapBase(CiscoBaseConnection):
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
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self,
        cmd: str = "write startup-config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config."""
        self.exit_config_mode()
        self.enable()
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class RaisecomRoapSSH(RaisecomRoapBase):
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


class RaisecomRoapTelnet(RaisecomRoapBase):
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
        assert isinstance(self.remote_conn, Telnet)
        self.remote_conn.set_option_negotiation_callback(self._process_option)
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
                    if re.search(
                        pri_prompt_terminator, output, flags=re.M
                    ) or re.search(alt_prompt_terminator, output, flags=re.M):
                        return return_msg

                # Check if proper data received
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                    alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                time.sleep(0.5 * delay_factor)
                i += 1
            except EOFError:
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
        self.remote_conn.close()
        raise NetmikoAuthenticationException(msg)
