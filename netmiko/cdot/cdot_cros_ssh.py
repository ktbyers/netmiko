#!/usr/bin/env python
# CDOT = Centre for Development of Telematics, India
# CROS = CDOT Router OS
# Script: cros_ssh.py
# Author: Maloy Ghosh <mghosh@cdot.in>
# Updated by Kirk Byers
#
# Purpose: Provide basic SSH connection to CROS based router products

from typing import Optional, Union, Sequence, Iterator, TextIO, Any
import time
import warnings
from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.base_connection import DELAY_FACTOR_DEPR_SIMPLE_MSG


class CdotCrosSSH(NoEnable, CiscoBaseConnection):
    """Implement methods for interacting with CROS network devices."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[#\$]")
        self.set_base_prompt()
        self._disable_complete_on_space()
        self.set_terminal_width(command="screen-width 511", pattern=r"screen.width 511")
        self.disable_paging(command="screen-length 0")
        return

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """CROS requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[#\$]",
        force_regex: bool = False,
    ) -> bool:
        """Checks if device is in configuration mode"""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def commit(
        self,
        comment: str = "",
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
        and_quit: bool = True,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        default:
           command_string = commit
        comment:
           command_string = commit comment <comment>

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        command_string = "commit"
        commit_marker = ["Commit complete", "No modifications to commit"]

        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            command_string += f' comment "{comment}"'

        output = self.config_mode()
        output += self._send_command_str(
            command_string,
            strip_prompt=False,
            strip_command=True,
            read_timeout=read_timeout,
        )

        if not (any(x in output for x in commit_marker)):
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        if and_quit:
            self.exit_config_mode()
        return output

    def _disable_complete_on_space(self) -> str:
        """
        CROS tries to auto complete commands when you type a "space" character.

        This is a bad idea for automation as what your program is sending no longer matches
        the command echo from the device. So we disable this behavior.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(delay_factor * 0.1)
        command = "complete-on-space false"
        self.write_channel(self.normalize_cmd(command))
        time.sleep(delay_factor * 0.1)
        output = self.read_channel()
        return output
