"""
DPtech (DeepInfo) Network Devices SSH and Telnet Driver for Netmiko.

This module provides support for DPtech (also known as DeepInfo) firewalls
and network devices. DPtech devices use a hierarchical view system:

    - User View: <hostname>
    - Control View (privileged): [hostname-XXX-M]           ← entered by "c"
    - Config Mode: [hostname-XXX-Developer-M]              ← entered by "_"

Usage:
    enable()      → sends "c"     → [hostname-...-M]
    config_mode() → sends "_"     → [hostname-...-Developer-M]
    exit          → sends "exit"  → back to control view or user view

Author: Netmiko Community
"""

import re
import time
from typing import Optional, Any, Union, Iterable

from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable


class DpTechBase(NoEnable, BaseConnection):
    """Base class for DPtech devices."""

    # Matches all possible prompts: <host>, [host...]
    prompt_pattern = r"<[^>]+>|\[[^\]]+\]"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.ansi_escape_codes = True

    def session_preparation(self) -> None:
        """Prepare session after connection."""
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command="screen-width 511", pattern=r"screen-width")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command: str = "terminal line 0", delay_factor: float = 1) -> str:
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def set_base_prompt(
        self,
        pri_prompt_terminator: Optional[str] = None,
        alt_prompt_terminator: Optional[str] = None,
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Extract hostname from <...> or [...] and set base_prompt as <hostname>."""
        if pattern is None:
            pattern = self.prompt_pattern

        prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern).strip()
        match = re.search(r"[<\[]([^>\]]+)[>\]]", prompt)
        if match:
            hostname = match.group(1).strip()
            if hostname:
                self.base_prompt = f"<{hostname}>"
                return self.base_prompt

        self.base_prompt = "<unknown>"
        return self.base_prompt

    def enable(
        self,
        cmd: str = "c",
        pattern: str = r"\[[^\]]+\]",
        re_flags: int = 0,
    ) -> str:
        """Enter control view using 'c'."""
        if not self.check_enable_mode():
            output = self.send_command_timing(
                cmd, strip_prompt=False, strip_command=False, read_timeout=10
            )
            self.set_base_prompt()
            if not self.check_enable_mode():
                raise ValueError("Failed to enter control view")
            return output
        return ""

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """Check if in control view: [hostname-...-M] but NOT containing 'Developer'."""
        prompt = self.find_prompt().strip()
        return prompt.startswith("[") and "Developer" not in prompt

    def exit_enable_mode(self, exit_command="exit"):
        """Exit enable mode (may require multiple 'exit' commands)."""
        if not self.check_enable_mode():
            return
        
        # Send 'exit' twice to ensure we get back to user view
        self.write_channel(exit_command + self.RETURN)
        self.read_until_pattern(pattern=r"[<\[].*?[>\]]", read_timeout=10)
        
        # Check if still in [ ] mode (config mode), send another exit if needed
        prompt = self.find_prompt()
        if prompt.startswith("["):
            self.write_channel(exit_command + self.RETURN)
            self.read_until_pattern(pattern=r"<.*>", read_timeout=10)

    def config_mode(
        self,
        config_command: str = "_",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enter configuration mode using '_'."""
        if self.check_config_mode():
            return ""
        if not self.check_enable_mode():
            self.enable()
        output = self.send_command_timing(
            config_command, strip_prompt=False, strip_command=False, read_timeout=10
        )
        self.set_base_prompt()
        if not self.check_config_mode():
            raise ValueError(f"Failed to enter configuration mode. Current prompt: {self.find_prompt()!r}")
        return output

    def exit_config_mode(self, exit_config: str = "exit", pattern: Optional[str] = None) -> str:
        """Exit config mode back to control view."""
        if not self.check_config_mode():
            return ""
        output = self.send_command_timing(
            exit_config, strip_prompt=False, strip_command=False, read_timeout=10
        )
        self.set_base_prompt()
        if self.check_config_mode():
            raise ValueError("Failed to exit configuration mode")
        return ""

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Check if in config mode: prompt contains 'Developer'."""
        prompt = self.find_prompt().strip()
        return prompt.startswith("[") and "Developer" in prompt

    def send_config_set(
        self,
        config_commands: Optional[Union[str, Iterable[str]]] = None,
        exit_config_mode: bool = True,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = True,
        strip_command: bool = True,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: Optional[str] = None,
        terminator: Optional[str] = None,
        bypass_commands: Optional[str] = None,
    ) -> str:
        """
        Send configuration commands to DPtech device.
        
        Properly handles str, list, tuple, generator, and other iterables.
        """
        if config_commands is None:
            return ""
        
        # Normalize config_commands to a list of strings
        if isinstance(config_commands, str):
            config_list = [config_commands]
        else:
            # Assume it's an iterable (list, tuple, generator, etc.)
            config_list = list(config_commands)
        
        # Ensure all items are strings and non-empty
        config_list = [str(cmd).strip() for cmd in config_list if str(cmd).strip()]
        if not config_list:
            return ""

        # Ensure we are in control view
        if not self.check_enable_mode():
            self.enable()

        # Enter config mode if needed
        if enter_config_mode:
            self.config_mode()

        # Get current config mode prompt for waiting
        config_prompt = self.find_prompt().strip()
        if not config_prompt.startswith("[") or "Developer" not in config_prompt:
            raise ValueError(f"Expected config prompt, got: {config_prompt!r}")

        # Escape regex special chars in prompt
        import re
        escaped_prompt = re.escape(config_prompt)
        expect_string = rf"{escaped_prompt}.*$"

        output = ""
        for cmd in config_list:
            # Send each command and wait for config prompt
            output += self.send_command(
                cmd,
                expect_string=expect_string,
                strip_prompt=strip_prompt,
                strip_command=strip_command,
                read_timeout=20,
            )

        # Exit config mode if requested
        if exit_config_mode:
            self.exit_config_mode()

        return output

    def find_prompt(self, delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        if pattern is None:
            pattern = self.prompt_pattern
        try:
            prompt = super().find_prompt(delay_factor=delay_factor, pattern=pattern)
        except Exception:
            prompt = super().find_prompt(delay_factor=delay_factor)
        return prompt.strip()

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = True,
        confirm_response: str = "y",
        read_timeout: float = 100.0,
    ) -> str:
        """Save config — must be in control view."""
        if not self.check_enable_mode():
            self.enable()

        if confirm:
            output = self._send_command_str(
                cmd, expect_string=r"(?:[Cc]ontinue\?|\[[^\]]+\])", read_timeout=read_timeout
            )
            if "continue" in output.lower():
                output += self._send_command_str(confirm_response, read_timeout=read_timeout)
        else:
            output = self._send_command_str(cmd, read_timeout=read_timeout)
        return output

    def cleanup(self, command: str = "exit") -> None:
        """Try to gracefully exit to user view."""
        try:
            if self.check_config_mode():
                self.exit_config_mode()
            if self.check_enable_mode():
                self.exit_enable_mode()
        except Exception:
            pass
        super().cleanup(command=command)


class DpTechSSH(DpTechBase):
    pass


class DpTechTelnet(DpTechBase):
    pass