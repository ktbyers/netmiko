import time
from socket import socket
from typing import Any

from netmiko.cisco_base_connection import CiscoBaseConnection
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
    Telnet,
)


class ZteZxrosBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()
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
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config Using Copy Run Start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class ZteZxrosSSH(ZteZxrosBase):
    pass


class ZteZxrosTelnet(ZteZxrosBase):
    @staticmethod
    def _process_option(telnet_sock: socket, cmd: bytes, opt: bytes) -> None:
        """
        ZTE need manually reply DO ECHO to enable echo command.
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
                # Width:500, Height:50
                telnet_sock.sendall(IAC + SB + NAWS + b"\x01\xf4\x00\x32" + IAC + SE)
            else:
                telnet_sock.sendall(IAC + WONT + opt)

    def telnet_login(self, *args: Any, **kwargs: Any) -> str:
        # set callback function to handle telnet options.
        assert isinstance(self.remote_conn, Telnet)
        self.remote_conn.set_option_negotiation_callback(self._process_option)  # type: ignore
        return super().telnet_login(*args, **kwargs)
