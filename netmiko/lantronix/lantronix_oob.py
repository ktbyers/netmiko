"""Lantronix out-of-band management products."""

import re

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class LantronixOobBase(NoEnable, NoConfig, BaseConnection):
    """Common methods for Lantronix OOB devices (SLC, EMG, SLB).

    Flat CLI with ``[<hostname]>`` prompt; no enable or config mode.
    """

    # [hostname]>
    prompt_pattern = r"\[[A-Za-z0-9_-]{1,64}\]>"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt(pattern=self.prompt_pattern)
        self.disable_paging(command="set cli terminallines disable")

    _LOGIN_USER = r"(?i)(?:user\s*name|user|login)\s*:"
    _LOGIN_PROMPT = r"\[[A-Za-z0-9_-]{1,64}\]>\s*$"

    def telnet_login(
        self,
        pri_prompt_terminator: str = "",
        alt_prompt_terminator: str = "",
        username_pattern: str = "",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        pri = pri_prompt_terminator or self._LOGIN_PROMPT
        alt = alt_prompt_terminator or self._LOGIN_PROMPT
        user = username_pattern or self._LOGIN_USER
        return super().telnet_login(
            pri_prompt_terminator=pri,
            alt_prompt_terminator=alt,
            username_pattern=user,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )

    def serial_login(
        self,
        pri_prompt_terminator: str = "",
        alt_prompt_terminator: str = "",
        username_pattern: str = "",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        pri = pri_prompt_terminator or self._LOGIN_PROMPT
        alt = alt_prompt_terminator or self._LOGIN_PROMPT
        user = username_pattern or self._LOGIN_USER
        self.write_channel(self.RETURN)
        output = self.read_channel()
        if re.search(pri, output, flags=re.M) or re.search(alt, output, flags=re.M):
            return output
        return super().serial_login(
            pri_prompt_terminator=pri,
            alt_prompt_terminator=alt,
            username_pattern=user,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )

    def save_config(
        self,
        cmd: str = "",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""
        if self.session_log:
            self.session_log.fin = True
        self.write_channel(command + self.RETURN)


class LantronixOobSSH(LantronixOobBase):
    pass


class LantronixOobTelnet(LantronixOobBase):
    pass


class LantronixOobSerial(LantronixOobBase):
    pass
