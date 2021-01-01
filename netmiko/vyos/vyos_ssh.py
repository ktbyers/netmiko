from typing import Any, Union, Iterable
import time
import io
from netmiko.cisco_base_connection import CiscoSSHConnection


class VyOSSSH(CiscoSSHConnection):
    """Implement methods for interacting with VyOS network devices."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width(command="set terminal width 512", pattern="terminal")
        self.disable_paging(command="set terminal length 0")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """No enable mode on VyOS."""
        return True

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on VyOS."""
        return ""

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on VyOS."""
        return ""

    def check_config_mode(self, check_string: str = "#", pattern: str = "") -> bool:
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = r"[edit]",
        re_flags: int = 0,
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(
        self, exit_config: str = "exit", pattern: str = r"exit"
    ) -> str:
        """Exit configuration mode"""
        output = ""
        if self.check_config_mode():
            output = self.send_command_timing(
                exit_config, strip_prompt=False, strip_command=False
            )
            if "Cannot exit: configuration modified" in output:
                output += self.send_command_timing(
                    "exit discard", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(self, comment: str = "", delay_factor: float = 0.1) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        default:
           command_string = commit
        comment:
           command_string = commit comment <comment>

        """
        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = ["Failed to generate committed config", "Commit failed"]
        command_string = "commit"

        if comment:
            command_string += f' comment "{comment}"'

        output = self.config_mode()
        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
        )

        if any(x in output for x in error_marker):
            raise ValueError(f"Commit failed with following errors:\n\n{output}")
        return output

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "$",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
    ) -> str:
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        # Set prompt to user@hostname (remove two additional characters)
        self.base_prompt = prompt[:-2].strip()
        return self.base_prompt

    def send_config_set(  # type: ignore
        self,
        config_commands: Union[str, Iterable[str], io.TextIOWrapper, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Remain in configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError
