"""A10 support."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class A10SSH(CiscoSSHConnection):
    """A10 support."""

    def session_preparation(self) -> None:
        """A10 requires to be enable mode to disable paging."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()

        # terminal width ill not do anything without A10 specific command
        # self.set_terminal_width()
        self.disable_paging(command="terminal length 0")

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError
