from typing import Any
from netmiko.base_connection import BaseConnection


class NetAppcDotSSH(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        cmd = self.RETURN + "rows 0" + self.RETURN
        self.disable_paging(command=cmd)

    def send_command_with_y(self, *args: Any, **kwargs: Any) -> str:
        output = self.send_command_timing(*args, **kwargs)
        if "{y|n}" in output:
            output += self.send_command_timing(
                "y", strip_prompt=False, strip_command=False
            )
        assert isinstance(output, str)
        return output

    def check_config_mode(self, check_string: str="*>", pattern: str = "") -> bool:
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str="set -privilege diagnostic -confirmations off", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(config_command=config_command, pattern=pattern, re_flags=re_flags)

    def exit_config_mode(self, exit_config: str="set -privilege admin -confirmations off", pattern: str = "") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on NetApp."""
        return ""

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """No enable mode on NetApp."""
        return True

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on NetApp."""
        return ""
