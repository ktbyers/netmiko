"""
AsterNOS platforms running Enterprise SONiC Distribution by AsterFusion Co.
"""

from typing import (
    Optional,
    Any,
)
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable


class AsterfusionAsterNOSSSH(NoEnable, CiscoSSHConnection):
    prompt_pattern = r"[>$#]"

    def __init__(self, _cli_mode: str = "klish", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cli_mode = _cli_mode

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt(alt_prompt_terminator="$")
        if self._cli_mode == "klish":
            self._enter_shell()
            self.disable_paging()
        elif self._cli_mode == "bash":
            self._enter_bash_cli()

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = r"\#",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_shell(self) -> str:
        return self._send_command_str("sonic-cli", expect_string=r"\#")

    def _enter_bash_cli(self) -> str:
        return self._send_command_str("system bash", expect_string=r"\$")

    def _enter_vtysh(self) -> str:
        return self._send_command_str("vtysh", expect_string=r"\#")

    def disable_paging(
        self,
        command: str = "terminal raw-output",
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

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = True,
        confirm_response: str = "y",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
