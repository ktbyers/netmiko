from typing import Optional
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class NetscalerSSH(NoConfig, BaseConnection):
    """Netscaler SSH class."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        cmd = f"{self.RETURN}set cli mode -page OFF{self.RETURN}"
        self.disable_paging(command=cmd)
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Sets self.base_prompt.

        Netscaler has only '>' for the prompt.
        """
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        # If null-string, set base_prompt to just ">"
        if not base_prompt:
            self.base_prompt = pri_prompt_terminator
        return self.base_prompt

    def strip_prompt(self, a_string: str) -> str:
        """Strip 'Done' from command output"""
        output = super().strip_prompt(a_string)
        lines = output.split(self.RESPONSE_RETURN)
        if "Done" in lines[-1]:
            return self.RESPONSE_RETURN.join(lines[:-1])
        else:
            return output
