from typing import Optional
import re
import warnings

from netmiko.base_connection import BaseConnection, DELAY_FACTOR_DEPR_SIMPLE_MSG


class EricssonIposSSH(BaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 512", pattern=r"terminal")
        self.disable_paging()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable 15",
        pattern="ssword",
        enable_pattern: Optional[str] = None,
        re_flags=re.IGNORECASE,
    ) -> str:
        return super().enable(
            cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
        )

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        """Ericsson IPOS requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def exit_enable_mode(self, exit_command="disable"):
        """
        Exits enable (privileged exec) mode.
        """
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=")#", pattern=""):
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """
        Exit from configuration mode.
        Ercisson output :
            end                   Commit configuration changes and return to exec mode
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def save_config(self, cmd="save config", confirm=True, confirm_response="yes"):
        """Saves configuration"""
        if confirm:
            output = self.send_command_timing(
                command_string=cmd, strip_prompt=False, strip_command=False
            )

            if confirm_response:
                output += self.send_command_timing(
                    confirm_response, strip_prompt=False, strip_command=False
                )
            else:
                output += self.send_command_timing(
                    self.RETURN, strip_prompt=False, strip_command=False
                )
        else:
            output = self.send_command(
                command_string=cmd, strip_prompt=False, strip_command=False
            )
        return output

    def commit(
        self,
        confirm: bool = False,
        confirm_delay=None,
        comment: str = "",
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ):
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """
        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)
        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check"
            )

        command_string = "commit"
        commit_marker = "Transaction committed"
        if confirm:
            if confirm_delay:
                command_string = f"commit confirmed {confirm_delay}"
            else:
                command_string = "commit confirmed"
            commit_marker = "Commit confirmed ,it will be rolled back within"

        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += f" comment {comment}"

        output = self.config_mode()

        output += self.send_command(
            command_string,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

        if commit_marker not in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        self.exit_config_mode()

        return output
