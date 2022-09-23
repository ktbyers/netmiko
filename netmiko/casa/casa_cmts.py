from typing import Optional
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable


class CasaCMTSBase(NoEnable, CiscoSSHConnection):
    """
    Casa CMTS support.

    Implements methods for interacting with Casa CMTS platforms.
    """

    def disable_paging(
        self,
        command: str = "page-off",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disables paging."""
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enters configuration mode."""
        return super().config_mode(
            config_command=config_command,
            pattern=pattern,
            re_flags=re_flags,
        )


class CasaCMTSSSH(CasaCMTSBase):
    """Casa CMTS SSH Driver."""

    pass
