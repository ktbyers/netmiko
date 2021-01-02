from typing import Optional
from netmiko.cisco_base_connection import CiscoSSHConnection


class QuantaMeshSSH(CiscoSSHConnection):
    def disable_paging(
        self,
        command: str = "no pager",
        delay_factor: float = 1.0,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging"""
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def save_config(
        self,
        cmd: str = "copy running-config startup-config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
