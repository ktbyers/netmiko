#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 - 2022 Kirk Byers
# Copyright (c) 2014 - 2022 Twin Bridges Technology
# Copyright (c) 2019 - 2020 NOKIA Inc.
# MIT License - See License file at:
#   https://github.com/ktbyers/netmiko/blob/develop/LICENSE

import re
import time
from typing import Any, Optional, Sequence, TextIO, Union
from netmiko import log
from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection


class NokiaSrlSSH(BaseConnection, NoEnable):
    """
    Implement methods for interacting with Nokia SRL devices for SSH.

    Not applicable in Nokia SRL:
        - check_enable_mode()
        - enable()
        - exit_enable_mode()

    Overriden methods to adapt Nokia SR OS behavior (changed):
        - session_preparation()
        - set_base_prompt()
        - config_mode()
        - exit_config_mode()
        - check_config_mode()
        - save_config()
        - commit()
        - strip_prompt()
        - enable()
        - check_enable_mode()

    By default, the SR Linux CLI prompt consists of two lines of text,
    indicating with an asterisk whether the configuration has been modified or
    a plus sign whether the configuration has been saved, the current mode and
    session type, the current CLI context, and the host name of the SR Linux device.

    Examples:

    --{ running }--[ interface ethernet-1/1 subinterface 1 ]--
    A:ams01#

    --{ * candidate private private-admin }--[ interface ethernet-1/1 subinterface 1 ]--
    A:ams01#

    --{ + candidate private private-admin }--[ interface ethernet-1/1 subinterface 1 ]--
    A:ams01#

    This class support the default prompt configuration.
    """

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.ansi_escape_codes = True
        # Bottom toolbar text not required
        command = "environment cli-engine type basic"
        self.write_channel(self.normalize_cmd(command))
        command = "environment complete-on-space false"
        self.write_channel(self.normalize_cmd(command))
        self.set_base_prompt()
        time.sleep(10 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"(\n\-\-\{.+\}\-\-\[.*\]\-\-\n.*# )",
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator, alt_prompt_terminator, delay_factor, pattern
        )

    def config_mode(
        self,
        config_command: str = "enter candidate private",
        pattern: str = "]--",
        re_flags: int = 0,
    ) -> str:

        output = super().config_mode(
            config_command=config_command, pattern="", re_flags=re_flags
        )
        return output

    def check_config_mode(
        self,
        check_string: str = r"\n--{( | \* | \+ | \+\* | \!\+ | \!\* )candidate",
        pattern: str = " ]--",
    ) -> bool:
        self.write_channel(self.RETURN)
        """
        supported first line prompt configuration:
        {modified_flags}{mode_and_session} }}--[ {pwc} ]
        """
        if not pattern:
            output = self.read_channel_timing(read_timeout=10.0)
        else:
            output = self.read_until_pattern(pattern=pattern)

        matches = re.search(check_string, output)
        return True if matches else False

    def commit(self) -> str:
        """Commit changes by using 'commit stay'."""
        cmd = "commit stay"
        self.write_channel(self.normalize_cmd(cmd))
        output = (
            self._get_cmd_output_and_prompt(cmd)
            if self.global_cmd_verify is not False
            else ""
        )
        return output

    def save_config(
        self,
        cmd: str = "save startup",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save current running configuration as initial (startup) configuration"""
        self.write_channel(self.normalize_cmd(cmd))
        output = (
            self._get_cmd_output_and_prompt(cmd)
            if self.global_cmd_verify is not False
            else ""
        )
        return output

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """Exit the candidate private mode"""
        output = ""
        self.write_channel(self.RETURN)
        prompt = self.read_until_pattern(pattern="]--")
        matches = re.search(r"\n--{( | \* | \+ | \+\* | \!\+ | \!\* )candidate", prompt)
        if matches:
            # In config mode and changes were made"""
            # Get the subgroup in matches. Should be only one.
            group = matches.group()
            if "*" in group:
                # Changes were made but not committed. Discarding changes
                output += self._discard()
            elif "+" in group:
                # Changes were made, committed and discarding is not available.
                # Committed changes can be saved in 'running mode'.
                log.warning(
                    """Exiting candidate private mode with unsaved changes!
                    Changes can be saved in running mode."""
                )
        # Switch to 'running' mode
        output += self._running_mode()
        return output

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Nokia SRL requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def _discard(self) -> str:
        """Discard changes made in candidate private mode"""
        log.warning("Uncommitted changes will be discarted!")
        cmd = "discard stay"
        self.write_channel(self.normalize_cmd(cmd))
        output = (
            self._get_cmd_output_and_prompt(cmd)
            if self.global_cmd_verify is not False
            else ""
        )
        return output

    def _running_mode(self) -> str:
        """Enter running mode"""
        cmd = "enter running"
        self.write_channel(self.normalize_cmd(cmd))
        output = (
            self._get_cmd_output_and_prompt(cmd)
            if self.global_cmd_verify is not False
            else ""
        )
        return output

    def _get_cmd_output_and_prompt(self, cmd: str = "") -> str:
        output = self.read_until_pattern(pattern=re.escape(cmd.strip()))
        output += self.read_until_prompt(read_entire_line=True)
        return output
