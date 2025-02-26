"""Adva F3 Device Support"""

import re
from typing import (
    Optional,
    Sequence,
    TextIO,
    Iterator,
    Union,
    Any,
)

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class AdvaAosFsp150F3SSH(NoEnable, NoConfig, CiscoSSHConnection):
    """
    Adva AOS FSP 15P F3 SSH Base Class

    F3 AOS applies for the following FSP150 device types:
    FSP150CC-XG21x
    FSP150CC-GE11x
    FSP150CC-GE20x

    These devices don't have a Enable Mode or Config Mode

    Configuration should be applied via the configuration context:

    home
    configure communication
    add ip-route nexthop xxxxxxx

    #
    #CLI:PORT N2A SHAPER-1-1-1-3-0  Create
    #
    home
    network-element ne-1

    Use of home to return to CLI root context
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        \n for default enter causes some issues with the Adva so setting to \r.
        """
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        Handles devices with security prompt enabled
        """
        data = self.read_until_pattern(pattern=r"Do you wish to continue \[Y\|N\]-->|-->")

        if "continue" in data:
            self.write_channel(f"y{self.RETURN}")
        else:
            self.write_channel(f"home{self.RETURN}")

        data = self.read_until_pattern(pattern=r"-->|--More--")

        if "--More--" in data:
            self.write_channel(self.RETURN)

        self.set_base_prompt()
        self.write_channel(self.RETURN)
        self.disable_paging(cmd_verify=False)

    def disable_paging(
        self,
        command: str = "",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Method to disable paging on the Adva, multi-line configuration command required."""

        if command:
            raise ValueError(f"Unexpected value for command in disable_paging() method: {command}")

        commands = [
            "configure user-security",
            f"config-user {self.username} cli-paging disabled",
            "home",
        ]
        return self.send_config_set(
            commands,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = r"-->",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        if pattern is None:
            if pri_prompt_terminator and alt_prompt_terminator:
                pri_term = re.escape(pri_prompt_terminator)
                alt_term = re.escape(alt_prompt_terminator)
                pattern = rf"({pri_term}|{alt_term})"
            elif pri_prompt_terminator:
                pattern = re.escape(pri_prompt_terminator)
            elif alt_prompt_terminator:
                pattern = re.escape(alt_prompt_terminator)

        if pattern:
            prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern)
        else:
            prompt = self.find_prompt(delay_factor=delay_factor)

        if not prompt[-3:] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")

        # If all we have is the 'terminator' just use that :-(
        if len(prompt) == 1:
            self.base_prompt = prompt
        else:
            # Strip off trailing terminator
            self.base_prompt = prompt[-3:]
        return self.base_prompt

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = False,
        read_timeout: Optional[float] = 2.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = False,
        error_pattern: str = "",
        terminator: str = None,
        bypass_commands: Optional[str] = None,
    ) -> str:

        if bypass_commands is None:
            categories = r"(?:superuser|crypto|maintenance|provisioning|retrieve|test-user)"
            bypass_commands = rf"(?:add\s+\S+\s+\S+\s+\S+\s+{categories}|secret.*)"

        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            read_timeout=read_timeout,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
            cmd_verify=cmd_verify,
            enter_config_mode=enter_config_mode,
            error_pattern=error_pattern,
            terminator=terminator,
            bypass_commands=bypass_commands,
        )

    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""
        return super().cleanup(command=command)
