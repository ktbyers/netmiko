"""Huawei SmartAX and OLT support."""

import time
import re
from typing import Optional, Any
from enum import Enum

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log


class Mode(Enum):
    """Define the mode of the device."""

    BASE = "base"
    ENABLE = "enable"
    CONFIG = "config"


class HuaweiSmartAXSSH(CiscoBaseConnection):
    """Supports Huawei SmartAX and OLT."""

    prompt_pattern = r"[>$]"

    def __init__(self, **kwargs: Any) -> None:
        self.mmi_mode = False
        if "mmi-mode" in kwargs:
            if not isinstance(kwargs["mmi-mode"], bool):
                raise ValueError("mmi-mode must be a boolean")
            self.mmi_mode = kwargs.get("mmi-mode", False)
            del kwargs["mmi-mode"]
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True

        data = self._test_channel_read(pattern=f"YES.NO|{self.prompt_pattern}")
        # Huawei OLT might put a post-login banner
        # that requires 'yes' to be sent.
        if re.search(r"YES.NO", data):
            self.write_channel(f"yes{self.RETURN}")
            self._test_channel_read(pattern=self.prompt_pattern)

        self.set_base_prompt()
        if self.mmi_mode:
            self.__send_command(
                command="mmi-mode enable",
                mode=Mode.CONFIG,
            )
        else:
            self.__send_command("undo smart")  # Disable autocomplete
            self.disable_paging("scroll")
            self.__send_command(  # Disable alarms
                command="infoswitch cli OFF",
                mode=Mode.ENABLE,
            )

    def __send_command(
        self, command: str, delay_factor: float = 1.0, mode: Mode = Mode.BASE
    ) -> None:
        """
        Send a command on startup to disable the automatic paging.
        """
        if mode in [Mode.ENABLE, Mode.CONFIG]:
            self.enable()
        if mode == Mode.CONFIG:
            self.config_mode()
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("Command: %s", command)
        self.write_channel(command)
        if self.global_cmd_verify is not False:
            output = self.read_until_pattern(pattern=re.escape(command.strip()))
        output = self.read_until_prompt(read_entire_line=True)
        log.debug("%s", output)
        if mode == Mode.CONFIG:
            self.exit_config_mode()
        if mode in [Mode.ENABLE, Mode.CONFIG]:
            self.exit_enable_mode()

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """
        Huawei does a strange thing where they add a space and then add ESC[1D
        to move the cursor to the left one.
        The extra space is problematic.
        """
        code_cursor_left = chr(27) + r"\[\d+D"
        output = string_buffer
        pattern = rf" {code_cursor_left}"
        output = re.sub(pattern, "", output)

        log.debug("Stripping ANSI escape codes")
        log.debug("new_output = %s", output)
        log.debug("repr = %s", repr(output))
        return super().strip_ansi_escape_codes(output)

    def config_mode(
        self, config_command: str = "config", pattern: str = r"\)#", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = "\\)#",
        pattern: str = "[#>]",
        force_regex: bool = True,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_config_mode(
        self, exit_config: str = "return", pattern: str = r"#.*"
    ) -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save Config for HuaweiSSH"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def cleanup(self, command: str = "quit") -> None:
        """
        Gracefully exit the SSH session.
        If mmi-mode is activated the session is automatically logged out.
        """
        super().cleanup(command=command)
        start_time = time.time()
        output: str = ""
        # If after 20 seconds the device hasn't logged out, force it
        while time.time() - start_time < 20 and not self.mmi_mode:
            output += self.read_channel()
            if output.endswith("Are you sure to log out? (y/n)[n]:"):
                self.write_channel("y" + self.RETURN)
                break
        output = ""
        start_time = time.time()
        while time.time() - start_time < 20:
            output += self.read_channel()
            if output.endswith("Configuration console exit, please retry to log on\n"):
                return
            time.sleep(0.01)
        raise ValueError("Failed to log out of the device")
