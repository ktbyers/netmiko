import io
from typing import Any, Union, Iterable

from netmiko.cisco_base_connection import CiscoSSHConnection


class CloudGenixIonSSH(CiscoSSHConnection):
    def establish_connection(self) -> None:
        self.channel.establish_connection(width=100, height=1000)

    def session_preparation(self, *args: Any, **kwargs: Any) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.write_channel(self.RETURN)
        self.set_base_prompt(delay_factor=5)

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Cloud Genix ION sets terminal height in establish_connection"""
        return ""

    def find_prompt(self, delay_factor: float = 1.0) -> str:
        prompt = super().find_prompt(delay_factor=delay_factor)
        prompt = self.strip_backspaces(prompt).strip()
        return prompt

    def strip_command(self, command_string: Any, output: Any) -> str:
        output = super().strip_command(command_string, output)
        # command_string gets repainted potentially multiple times (grab everything after last one)
        output = output.split(command_string)[-1]
        return output

    def check_config_mode(self, *args: Any, **kwargs: Any) -> bool:
        """Devices do not have a config mode."""
        return False

    def config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Devices do not have a config mode."""
        return ""

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Devices do not have a config mode."""
        return ""

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """No save method on ION SSH"""
        return ""

    def send_config_set(
        self,
        config_commands: Union[str, Iterable[str], io.TextIOWrapper, None] = None,
        exit_config_mode: bool = False,
        *args: Any,
        **kwargs: Any
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )
