from typing import Any

from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection


class NetAppcDotSSH(NoEnable, BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        cmd = self.RETURN + "rows 0" + self.RETURN
        self.disable_paging(command=cmd)

    def send_command_with_y(self, *args: Any, **kwargs: Any) -> str:
        output = self._send_command_timing_str(*args, **kwargs)
        if "{y|n}" in output:
            output += self._send_command_timing_str(
                "y", strip_prompt=False, strip_command=False
            )
        return output

    def check_config_mode(
        self, check_string: str = "*>", pattern: str = "", force_regex: bool = False
    ) -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "set -privilege diagnostic -confirmations off",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(
        self,
        exit_config: str = "set -privilege admin -confirmations off",
        pattern: str = "",
    ) -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)
