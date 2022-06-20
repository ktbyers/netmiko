from typing import Optional, Any
import warnings
from netmiko.base_connection import DELAY_FACTOR_DEPR_SIMPLE_MSG
from netmiko.cisco_base_connection import CiscoSSHConnection


class EltexEsrSSH(CiscoSSHConnection):
    """Netmiko support for routers Eltex ESR."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump")

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = r"\)\#",
        re_flags: int = 0,
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = "(config",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented (use commit() method)"""
        raise NotImplementedError

    def commit(
        self, read_timeout: float = 120.0, delay_factor: Optional[float] = None
    ) -> str:
        """
        Commit the candidate configuration.
        Commit the entered configuration.
        Raise an error and return the failure
        if the commit fails.
        default:
           command_string = commit

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        error_marker = "Can't commit configuration"
        command_string = "commit"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self._send_command_str(
            command_string=command_string, read_timeout=read_timeout
        )

        if error_marker in output:
            raise ValueError(
                "Commit failed with following errors:\n\n{}".format(output)
            )
        return output

    def _confirm(
        self, read_timeout: float = 120.0, delay_factor: Optional[float] = None
    ) -> str:
        """
        Confirm the candidate configuration.
        Raise an error and return the failure if the confirm fails.

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        error_marker = "Nothing to confirm in configuration"
        command_string = "confirm"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self._send_command_str(
            command_string=command_string, read_timeout=read_timeout
        )

        if error_marker in output:
            raise ValueError(
                "Confirm failed with following errors:\n\n{}".format(output)
            )
        return output

    def _restore(
        self, read_timeout: float = 120.0, delay_factor: Optional[float] = None
    ) -> str:
        """
        Restore the candidate configuration.

        Raise an error and return the failure if the restore fails.

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        error_marker = "Can't find backup of previous configuration!"
        command_string = "restore"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self._send_command_str(
            command_string=command_string, read_timeout=read_timeout
        )

        if error_marker in output:
            raise ValueError(
                "Restore failed with following errors:\n\n{}".format(output)
            )
        return output
