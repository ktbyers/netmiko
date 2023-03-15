from typing import Optional

from netmiko.cisco_base_connection import CiscoBaseConnection


class FsosV2SSH(CiscoBaseConnection):
    """
    Implements methods for communicating with Fsos v2.

    Mostly conforms to Cisco IOS style syntax with a few minor changes.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        cmd = "terminal width 256"
        self.set_base_prompt()
        """Fsos v2 requires enable mode to set terminal width"""
        self.enable()
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = base_prompt
        return self.base_prompt

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config Using write"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
