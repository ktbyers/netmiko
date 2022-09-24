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

    def exit_config_mode(
        self, exit_config: str = chr(26), pattern: str = r"#.*"
    ) -> str:
        """
        Exits configuration mode.

        Must use CTRL-Z (ASCII 26) to reliably exit from any
        tier in the configuration hierarchy.

        Since CTRL-Z is a non-printable character, we must temporarily disable
        global_cmd_verify to prevent an exception trying to read the
        echoed input.
        """
        if self.global_cmd_verify is not False and exit_config == chr(26):
            global_cmd_verify_tmp = self.global_cmd_verify
            self.global_cmd_verify = False
            output = super().exit_config_mode(exit_config, pattern)
            self.global_cmd_verify = global_cmd_verify_tmp
        else:
            output = super().exit_config_mode(exit_config, pattern)
        return output


class CasaCMTSSSH(CasaCMTSBase):
    """Casa CMTS SSH Driver."""

    pass
