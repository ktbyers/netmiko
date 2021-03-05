from typing import Any

from netmiko.cisco_base_connection import CiscoSSHConnection


class CoriantSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        raise AttributeError("Coriant devices do not support enable mode!")

    def enable(self, *args: Any, **kwargs: Any) -> str:
        raise AttributeError("Coriant devices do not support enable mode!")

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        raise AttributeError("Coriant devices do not support enable mode!")

    def check_config_mode(self, *args: Any, **kwargs: Any) -> bool:
        """Coriant devices do not have a config mode."""
        return False

    def config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Coriant devices do not have a config mode."""
        return ""

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Coriant devices do not have a config mode."""
        return ""

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ":",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 2.0,
    ) -> str:
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        return self.base_prompt

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Not Implemented"""
        raise NotImplementedError
