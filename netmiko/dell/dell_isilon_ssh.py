from typing import Any, Optional
import time
import re

from netmiko.base_connection import BaseConnection


class DellIsilonSSH(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[#\$]")
        self._zsh_mode()
        self.find_prompt()
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "$",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Determine base prompt."""
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """Remove Null code"""
        output = re.sub(r"\x00", "", string_buffer)
        return super().strip_ansi_escape_codes(output)

    def _zsh_mode(self, prompt_terminator: str = "$") -> None:
        """Run zsh command to unify the environment"""
        if self.global_delay_factor < 1:
            delay_factor = 1.0
        else:
            delay_factor = self.global_delay_factor
        command = self.RETURN + "zsh" + self.RETURN
        self.write_channel(command)
        time.sleep(0.25 * delay_factor)
        self._set_prompt(prompt_terminator)
        time.sleep(0.25 * delay_factor)
        self.clear_buffer()

    def _set_prompt(self, prompt_terminator: str = "$") -> None:
        prompt = f"PROMPT='%m{prompt_terminator}'"
        command = self.RETURN + prompt + self.RETURN
        self.write_channel(command)

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Isilon doesn't have paging by default."""
        return ""

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "sudo su",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:

        delay_factor = self.select_delay_factor(delay_factor=1)
        output = ""

        if check_state and self.check_enable_mode():
            return output

        output += self._send_command_timing_str(
            cmd, strip_prompt=False, strip_command=False
        )
        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.normalize_cmd(self.secret))
        output += self.read_until_pattern(pattern=r"#.*$")
        time.sleep(1 * delay_factor)
        self._set_prompt(prompt_terminator="#")
        if not self.check_enable_mode():
            raise ValueError("Failed to enter enable mode")

        return output

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(
        self, check_string: str = "#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Use equivalent enable method."""
        return self.check_enable_mode(check_string=check_string)

    def config_mode(
        self,
        config_command: str = "sudo su",
        pattern: str = "ssword",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Use equivalent enable method."""
        return self.enable(cmd=config_command, pattern=pattern, re_flags=re_flags)

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        """Use equivalent enable method."""
        return self.exit_enable_mode(exit_command=exit_config)
