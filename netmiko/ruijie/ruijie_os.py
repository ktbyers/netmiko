"""Ruijie RGOS Support"""
import time
from typing import Any, Optional
import re

from netmiko.cisco_base_connection import CiscoBaseConnection


class RuijieOSBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        """Ruijie OS requires enable mode to set terminal width"""
        self.enable()
        self.set_terminal_width(command="terminal width 256", pattern="terminal")
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save config: write"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        # param enable_special_pattern: the pattern used to search for special enable handler, such as change the eanble password
        # type pattern: regular expression string
        enable_special_pattern = "change the password"

        # Check if in enable mode
        if not self.check_enable_mode():
            # Send "enable" mode command
            self.write_channel(self.normalize_cmd(cmd))
            try:
                # Read the command echo
                end_data = ""
                if self.global_cmd_verify is not False:
                    output += self.read_until_pattern(pattern=re.escape(cmd.strip()))
                    end_data = output.split(cmd.strip())[-1]

                # Search for trailing prompt or password pattern
                if pattern not in output and self.base_prompt not in end_data:
                    output += self.read_until_prompt_or_pattern(
                        pattern=pattern, re_flags=re_flags
                    )

                # Send the "secret" in response to password pattern
                if re.search(pattern, output):
                    self.write_channel(self.normalize_cmd(self.secret))
                    output += self.read_until_prompt_or_pattern(
                        pattern=enable_special_pattern, re_flags=re_flags
                    )

                # Search for special login handler
                if re.search(enable_special_pattern, output):
                    self.write_channel(self.normalize_cmd("no"))
                    output += self.read_until_prompt()

                # Search for terminating pattern if defined
                if enable_pattern and not re.search(enable_pattern, output):
                    output += self.read_until_pattern(pattern=enable_pattern)
                else:
                    if not self.check_enable_mode():
                        raise ValueError(msg)

            except NetmikoTimeoutException:
                raise ValueError(msg)
        return output

    def special_login_handler(self):
        """Handle password change request by ignoring it"""
        # Ruijie can prompt for password change. Search for that or for normal prompt
        password_change_prompt = r"(change the password)|([>#]\s*$)"
        output = self.read_until_pattern(password_change_prompt)
        if re.search(password_change_prompt, output):
            self.write_channel("no\n")
            self.clear_buffer()
        return output

class RuijieOSSSH(RuijieOSBase):

    pass


class RuijieOSTelnet(RuijieOSBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
