import time
import re
from typing import Any, Optional

from netmiko.base_connection import BaseConnection


class YamahaBase(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="console lines infinity")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "administrator",
        pattern: str = r"Password",
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

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """
        When any changes have been made, the prompt 'Save new configuration ? (Y/N)'
        appears before exiting. Ignore this by entering 'N'.
        """
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            time.sleep(1)
            output = self.read_channel()
            if "(Y/N)" in output:
                self.write_channel("N")
            if self.base_prompt not in output:
                output += self.read_until_prompt(read_entire_line=True)
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(
        self, check_string: str = "#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in administrator mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "administrator",
        pattern: str = "Password",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return self.enable(cmd=config_command, pattern=pattern, re_flags=re_flags)

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = ">") -> str:
        """
        No action taken. Call 'exit_enable_mode()' to explicitly exit Administration
        Level.
        """
        return ""

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config."""
        if confirm is True:
            raise ValueError("Yamaha does not support save_config confirmation.")
        self.enable()
        # Some devices are slow so match on trailing-prompt if you can
        return self._send_command_str(command_string=cmd)


class YamahaSSH(YamahaBase):
    """Yamaha SSH driver."""

    pass


class YamahaTelnet(YamahaBase):
    """Yamaha Telnet driver."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
