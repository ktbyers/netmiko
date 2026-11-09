from typing import Any, Optional
from netmiko.cisco_base_connection import CiscoSSHConnection


class SilverPeakVXOASSH(CiscoSSHConnection):
    prompt_pattern = r"[>#]"

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        return super().__init__(**kwargs)

    def find_prompt(self, delay_factor: float = 1.0, pattern: Optional[str] = "") -> str:
        if not pattern:
            pattern = self.prompt_pattern
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no cli session paging enable")

    def check_config_mode(
        self,
        check_string: str = "(config) #",
        pattern: str = prompt_pattern,
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Silverpeak uses "(<controller name>) (config) #" as config prompt
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#.*") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)
