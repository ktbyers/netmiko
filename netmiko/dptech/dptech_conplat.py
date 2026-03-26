"""
DPtech (DeepInfo) Network Devices SSH and Telnet Driver for Netmiko.

This module provides support for DPtech (also known as DeepInfo) firewalls
and network devices. DPtech devices use a hierarchical view system similar to
Huawei, with different prompt formats for various operational modes.

Supported Views and Prompt Formats:
    - User View (普通视图): <hostname>
    - Control View (控制视图): [hostname] - privileged mode
    - Configuration Mode (配置模式): [hostname-config] - system configuration

"""

import re
import time
from typing import Any, Iterator, Optional, Sequence, TextIO, Union

from netmiko.base_connection import BaseConnection


class DpTechConplatBase(BaseConnection):
    """
    Base connection class for DPtech (DeepInfo) network devices.

    This class implements device-specific handling for DPtech firewalls
    and network equipment, including prompt pattern recognition, view
    management, and configuration operations.

    Attributes:
        prompt_pattern: Regular expression matching DPtech prompts in both
            user view (<hostname>) and control view ([hostname]).
    """

    # Prompt patterns for DPtech devices
    # Matches both user view: <hostname> and control view: [hostname]
    prompt_pattern = r"<[^>]+>|\[[^\]]+\]"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize DPtech connection with ANSI escape code support."""
        super().__init__(*args, **kwargs)
        self.ansi_escape_codes = True

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="terminal line 0")
        self.set_terminal_width(command="screen-width 511", pattern=r"screen-width")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "]",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        return prompt.strip()

    def enable(
        self,
        cmd: str = "c",
        pattern: str = r"\[" + r"[^\]]+\]",
        re_flags: int = 0,
        check_state: bool = True,
    ) -> str:
        """
        Enter control view (privileged mode) on DPtech devices.

        The control view provides elevated privileges similar to
        Cisco's enable mode. In this view, users can execute
        configuration commands and view sensitive information.
        """
        output = self.send_command_timing(
            cmd, strip_prompt=False, strip_command=False, read_timeout=30
        )
        if check_state and not self.check_enable_mode():
            raise ValueError("Failed to enter control view")
        return output

    def check_enable_mode(self, check_string: str = "") -> bool:
        """Check if in control view: prompt is [hostname-M] (not config mode).

        DPtech prompts:
        - User view: <hostname>
        - Control view: [hostname-M] where M is at the end (total 9 parts)
        - Config mode: [hostname-word-M] where word != M is before the final M (total 10+ parts)
        """
        prompt = self.find_prompt()
        if not prompt.startswith("["):
            return False
        inner_parts = prompt[1:-1].split("-")
        # Control view: 9 parts (hostname ends with -M) and ends with -M
        # Config mode: 10+ parts (extra word before final -M)
        return len(inner_parts) == 9 and inner_parts[-1] == "M"

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit enable mode (control view or config mode) back to user view.

        DPtech devices use 'exit' command:
        - From config mode -> control view (need to exit again)
        - From control view -> user view

        If in config mode, exit first. Then always exit from control view.
        """
        output = ""
        if self.check_config_mode():
            # In config mode, exit to control view
            output += self.send_command_timing(
                exit_command, strip_prompt=False, strip_command=False, read_timeout=30
            )
        if self.check_enable_mode():
            # In control view, exit to user view
            output += self.send_command_timing(
                exit_command, strip_prompt=False, strip_command=False, read_timeout=30
            )
        return output

    def config_mode(
        self,
        config_command: str = "_",
        pattern: str = r"-M\]",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"\]") -> str:
        """Exit config mode using 'exit' command."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Check if in config mode: prompt is [hostname-word-M] where word is NOT part of hostname.

        Config mode has an extra word before the final -M.
        Control: [hostname-M] -> len=9, parts[-2]=hostname_last, parts[-1]=M
        Config: [hostname-word-M] -> len=10, parts[-2]=word, parts[-1]=M
        """
        prompt = self.find_prompt()
        if not prompt.startswith("["):
            return False
        inner_parts = prompt[1:-1].split("-")
        # Config mode: more than 9 parts and ends with -M (extra word before M)
        return len(inner_parts) > 9 and inner_parts[-1] == "M"

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        **kwargs: Any,
    ) -> str:
        """Send configuration commands using send_command_timing for better compatibility."""
        if config_commands is None:
            return ""
        # Convert single command to list
        if isinstance(config_commands, str):
            config_commands = [config_commands]

        output = ""
        for cmd in config_commands:
            output += self.send_command_timing(
                cmd, strip_prompt=False, strip_command=False, read_timeout=30
            )
        if exit_config_mode:
            self.exit_config_mode()
        return output

    def find_prompt(self, delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        """
        Find the current device prompt.

        Supports both DPtech prompt formats:
            - User view: <hostname>
            - Control view: [hostname]

        Args:
            delay_factor: Delay factor for prompt detection
            pattern: Optional custom regex pattern

        Returns:
            The current prompt string
        """
        if pattern is None:
            pattern = self.prompt_pattern
        prompt = super().find_prompt(delay_factor=delay_factor, pattern=pattern)
        return prompt.strip()

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = True,
        confirm_response: str = "y",
        read_timeout: float = 100.0,
    ) -> str:

        self.enable()

        if confirm:
            pattern = rf"(?:[Cc]ontinue|{self.prompt_pattern})"
            output = self._send_command_str(
                command_string=cmd,
                expect_string=pattern,
                strip_prompt=False,
                strip_command=False,
                read_timeout=read_timeout,
            )
            if confirm_response and re.search(r"[Cc]ontinue", output):
                output += self._send_command_str(
                    command_string=confirm_response,
                    expect_string=self.prompt_pattern,
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=read_timeout,
                )
        else:
            output = self._send_command_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
                read_timeout=read_timeout,
            )
        return output

    def cleanup(self, command: str = "quit") -> None:
        return super().cleanup(command=command)


class DpTechConplatSSH(DpTechConplatBase):
    pass


class DpTechConplatTelnet(DpTechConplatBase):
    pass
