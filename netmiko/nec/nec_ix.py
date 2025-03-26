import time
import re
from socket import socket
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
from typing import Any, Optional

from netmiko.base_connection import BaseConnection


class NecIxBase(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.enable()
        time.sleep(0.3 * self.global_delay_factor)
        self.config_mode()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()
        self.disable_paging(command=self.RETURN + "terminal length 0")

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Cisco IOS/IOS-XE abbreviates the prompt at 20-chars in config mode.
        Consequently, abbreviate the base_prompt
        """
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = base_prompt[:16]
        return self.base_prompt

    def enable(
        self,
        cmd: str = "svintr-config",
        pattern: str = "",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        There are several commands to enter the enable mode,
        NEC IX enable mode is the same as configuration mode.
        svintr-config   -- Enter configuration mode (supervisor interrupt)
        enable-config   -- Enter configuration mode
        configure       -- Enter configuration mode
        """
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def check_enable_mode(self, check_string: str = ")#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exits enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            time.sleep(1)
            output = self.read_channel()
            if ")#" in output:
                self.write_channel("exit")
            if self.base_prompt not in output:
                output += self.read_until_prompt(read_entire_line=True)
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """configure command is used to go to the top menu in configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in Configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def exit_config_mode(
        self, exit_config: str = "configure", pattern: str = ""
    ) -> str:
        """
        When you exit configuration mode, the show commands available to you are limited.
        Therefore, use the configure command to go to the top menu.
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            time.sleep(1)
            if self.base_prompt not in output:
                output += self.read_until_prompt(read_entire_line=True)
        return output

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        self.config_mode()
        output = self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
            read_timeout=100.0,
        )
        return output


class NecIxSSH(NecIxBase):
    """NecIx SSH driver."""

    pass


class NecIxTelnet(NecIxBase):
    """NecIx Telnet driver."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)

    def _process_option(self, telnet_sock: socket, cmd: bytes, opt: bytes) -> None:
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
        username_pattern: str = r"login",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        assert isinstance(self.remote_conn, Telnet)
        self.remote_conn.set_option_negotiation_callback(self._process_option)  # type: ignore
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
