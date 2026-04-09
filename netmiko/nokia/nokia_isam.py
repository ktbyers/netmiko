import time
import re
from typing import Any

from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable


class NokiaIsamSSH(BaseConnection, NoEnable):
    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        commands = [
            "environment mode batch",
            "exit",
        ]
        for command in commands:
            self.disable_paging(command=command, cmd_verify=True, pattern=r"#")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"\*?(.*?)(>.*)*#", cur_base_prompt)
        if match:
            # strip off >... from base_prompt; strip off leading *
            self.base_prompt: str = match.group(1)

        return self.base_prompt

    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""
        try:
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final command
        if self.session_log:
            self.session_log.fin = True
        self.write_channel(command + self.RETURN)

    def check_config_mode(
        self,
        check_string: str = ">configure",
        pattern: str = "#",
        force_regex: bool = False,
    ) -> bool:
        """Use equivalent enable method."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit all", pattern: str = "") -> str:
        return super().exit_config_mode(exit_config=exit_config)

    def save_config(
        self, cmd: str = "admin save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        return self._send_command_str(
            command_string=cmd,
            strip_prompt=False,
            strip_command=False,
        )
