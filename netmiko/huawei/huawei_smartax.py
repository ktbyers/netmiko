import time
import re
from typing import Optional

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log


class HuaweiSmartAXSSH(CiscoBaseConnection):
    """Supports Huawei SmartAX and OLT."""

    prompt_pattern = r"[>$]"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True

        data = self._test_channel_read(pattern=f"YES.NO|{self.prompt_pattern}")
        # Huawei OLT might put a post-login banner that requires 'yes' to be sent.
        if re.search(r"YES.NO", data):
            self.write_channel(f"yes{self.RETURN}")
            self._test_channel_read(pattern=self.prompt_pattern)

        self.set_base_prompt()
        self._disable_smart_interaction()
        self.disable_paging()

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
        log.debug(f"new_output = {output}")
        log.debug(f"repr = {repr(output)}")
        return super().strip_ansi_escape_codes(output)

    def _disable_smart_interaction(
        self, command: str = "undo smart", delay_factor: float = 1.0
    ) -> None:
        """Disables the { <cr> } prompt to avoid having to sent a 2nd return after each command"""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("In disable_smart_interaction")
        log.debug(f"Command: {command}")
        self.write_channel(command)
        if self.global_cmd_verify is not False:
            output = self.read_until_pattern(pattern=re.escape(command.strip()))
            output = self.read_until_prompt(read_entire_line=True)
        else:
            output = self.read_until_prompt(read_entire_line=True)
        log.debug(f"{output}")
        log.debug("Exiting disable_smart_interaction")

    def disable_paging(
        self,
        command: str = "scroll",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        return super().check_config_mode(check_string=check_string)

    def exit_config_mode(
        self, exit_config: str = "return", pattern: str = r"#.*"
    ) -> str:
        return super().exit_config_mode(exit_config=exit_config)

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
