from typing import Any, Sequence, TextIO, Union
from netmiko.cisco_base_connection import CiscoSSHConnection


class ZyxelSSH(CiscoSSHConnection):
    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """No paging on Zyxel"""
        pass

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """No enable mode on Zyxel."""
        pass

    def enable(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on Zyxel."""
        pass

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """No enable mode on Zyxel."""
        pass

    def config_mode(self, *args: Any, **kwargs: Any) -> str:
        """No config mode on Zyxel"""
        return ""

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """No config mode on Zyxel"""
        pass

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        enter_config_mode: bool = False,
        **kwargs: Any
    ) -> str:
        """No config mode on Zyxel"""
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            enter_config_mode=enter_config_mode,
            **kwargs
        )
