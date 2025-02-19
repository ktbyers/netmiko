#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 - 2022 Kirk Byers
# Copyright (c) 2014 - 2022 Twin Bridges Technology
# Copyright (c) 2019 - 2022 NOKIA Inc.
# MIT License - See License file at:
#   https://github.com/ktbyers/netmiko/blob/develop/LICENSE

import re
from typing import Any, Optional, Sequence, Iterator, TextIO, Union
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
        self._test_channel_read(pattern=r"#")
        self.ansi_escape_codes = True
        # Bottom toolbar text not required
        commands = [
            "environment complete-on-space false",
            "environment cli-engine type basic",
        ]
        for command in commands:
            self.disable_paging(command=command, cmd_verify=True, pattern=r"#")
        self.set_base_prompt()

    def strip_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Strip the prompt and the additional context line"""
        a_string = super().strip_prompt(*args, **kwargs)
        return self._strip_context_items(a_string)

    def _strip_context_items(self, a_string: str) -> str:
        """Strip NokiaSRL-specific output.

        Nokia will put extra context in the 1st line of the prompt, such as:
        --{ running }--[  ]--
        --{ candidate private private-admin }--[  ]--
        --{ candidate private private-admin }--[  ]--

        This method removes those lines.
        """
        strings_to_strip = [
            r"--{.*\B",
        ]

        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        for pattern in strings_to_strip:
            if re.search(pattern, last_line, flags=re.I):
                return self.RESPONSE_RETURN.join(response_list[:-1])
        return a_string

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = r"#",
    ) -> str:
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def config_mode(
        self,
        config_command: str = "enter candidate private",
        pattern: str = r"#",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self,
        check_string: str = r"\n--{( | \* | \+ | \+\* | \!\+ | \!\* | \+\!\* | \+\! )candidate",
        pattern: str = r"#",
        force_regex: bool = True,
    ) -> bool:

        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def commit(self) -> str:
        """Commit changes by using 'commit stay'."""
        cmd = "commit stay"
        output = self._send_command_str(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        return output

    def save_config(
        self,
        cmd: str = "save startup",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save current running configuration as initial (startup) configuration"""
        return self._send_command_str(
            command_string=cmd, strip_prompt=False, strip_command=False
        )

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """Exit the candidate private mode"""
        output = ""
        self.write_channel(self.RETURN)
        prompt = self.read_until_pattern(pattern="#")

        if self._has_uncommitted_changes(prompt):
            # Changes were made but not committed. Discarding changes
            output += self._discard()
        # Switch to 'running' mode
        output += self._running_mode()
        return output

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
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
        output = self._send_command_str(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        return output

    def _running_mode(self) -> str:
        """Enter running mode"""
        cmd = "enter running"
        output = self._send_command_str(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        return output

    def _has_uncommitted_changes(self, prompt: str) -> bool:
        """
        The asterix (*) next to the mode name indicates that the candidate configuration
        has changes that have not yet been committed.

        The plus sign (+) in the prompt indicates that the running configuration differs
        from the startup configuration. After you enter the save startup command,
        the running configuration is synchronized with the startup configuration,
        and the plus sign is removed from the prompt.

        The exclamation mark (!) in the prompt indicates that another user has commited
        changes to the running datastore.
        """
        matches = re.search(
            r"\n--{( | \* | \+ | \+\* | \!\+ | \!\* | \+\!\* | \+\! )candidate", prompt
        )
        return True if matches and "*" in matches.group() else False
