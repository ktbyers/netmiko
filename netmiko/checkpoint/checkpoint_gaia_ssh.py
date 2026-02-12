import time
import re
from typing import Optional, Any

from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class CheckPointGaiaSSH(NoConfig, BaseConnection):
    """
    Implements methods for communicating with Check Point Gaia
    firewalls.
    """

    prompt_pattern = r"[>#]"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Kept running into issues with command_echo and duplicate echoes of commands.
        self.fast_cli = False
        fast_cli = kwargs.get("fast_cli") or False
        kwargs["fast_cli"] = fast_cli
        return super().__init__(*args, **kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('>').
        """
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="set clienv rows 0")

        # Clear read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            if self.check_enable_mode():
                self.exit_enable_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        if self.session_log:
            self.session_log.fin = True
        self.write_channel(command + self.RETURN)

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable_secret_handler(
        self,
        pattern: str,
        output: str,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        Check Point Gaia requires very particular timing for this 'expert'
        password handling to work.

        Send the "secret" in response to password pattern
        """
        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.secret)
            time.sleep(0.3 * self.global_delay_factor)
            self.write_channel(self.RETURN)
            time.sleep(0.3 * self.global_delay_factor)
            new_output = self.read_until_pattern(pattern=self.prompt_pattern)
        return new_output

    def enable(
        self,
        cmd: str = "expert",
        pattern: str = r"expert password",
        enable_pattern: Optional[str] = r"\#",
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        Enter expert mode.

        Check Point Gaia is very finicky on the timing of sending this 'expert' password.
        """
        output = super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )
        self.set_base_prompt()
        return output

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit expert mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_pattern(pattern=r">")
            self.set_base_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd("exit"))
            output += self.read_until_pattern(pattern=r">")
            self.set_base_prompt()

        output += self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
            read_timeout=100.0,
        )
        return output
