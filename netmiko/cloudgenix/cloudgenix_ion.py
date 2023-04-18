from typing import Any, Union, Sequence, Iterator, TextIO, Optional
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class CloudGenixIonSSH(NoConfig, CiscoSSHConnection):
    def establish_connection(self, width: int = 100, height: int = 1000) -> None:
        super().establish_connection(width=width, height=height)

    def session_preparation(self, *args: Any, **kwargs: Any) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.write_channel(self.RETURN)
        self.set_base_prompt(delay_factor=5)

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Cloud Genix ION sets terminal height in establish_connection"""
        return ""

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        prompt = super().find_prompt(delay_factor=delay_factor, pattern=pattern)
        prompt = self.strip_backspaces(prompt).strip()
        return prompt

    def strip_command(self, command_string: str, output: str) -> str:
        output = super().strip_command(command_string, output)
        # command_string gets repainted potentially multiple times (grab everything after last one)
        output = output.split(command_string)[-1]
        return output

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )
