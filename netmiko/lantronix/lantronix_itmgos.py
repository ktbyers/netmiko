"""Lantronix IT Management Gateway OS (ITMGOS).

Covers SLC, EMG, and SLB products that share one flat CLI.
Tested with SLC9032, SLC8016, EMG851202, EMG751201, and SLB882.
"""

import re

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class LantronixItmgOsBase(NoEnable, NoConfig, BaseConnection):
    """Common methods for Lantronix ITMGOS devices (SLC, EMG, SLB).

    Flat CLI with ``[<hostname>]>`` prompt; no enable or config mode.
    """

    # [hostname]>
    prompt_pattern = r"\[[\w-]{1,64}\]>"
    login_prompt_pattern = prompt_pattern + r"\s*$"
    _LOGIN_USER = r"(?i)(?:username|user name|user|login)\s*:"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt(pattern=self.prompt_pattern)
        self.disable_paging(command="set cli terminallines disable")

    def telnet_login(
        self,
        pri_prompt_terminator: str = "",
        alt_prompt_terminator: str = "",
        username_pattern: str = "",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        if not pri_prompt_terminator:
            pri_prompt_terminator = self.login_prompt_pattern
        if not alt_prompt_terminator:
            alt_prompt_terminator = self.login_prompt_pattern
        if not username_pattern:
            username_pattern = self._LOGIN_USER
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
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
        if not pri_prompt_terminator:
            pri_prompt_terminator = self.login_prompt_pattern
        if not alt_prompt_terminator:
            alt_prompt_terminator = self.login_prompt_pattern
        if not username_pattern:
            username_pattern = self._LOGIN_USER
        self.write_channel(self.RETURN)
        output = self.read_channel()
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return output
        return super().serial_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
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


class LantronixItmgOsSSH(LantronixItmgOsBase):
    pass


class LantronixItmgOsTelnet(LantronixItmgOsBase):
    pass


class LantronixItmgOsSerial(LantronixItmgOsBase):
    pass
