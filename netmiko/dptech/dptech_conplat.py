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
from typing import Optional, Any

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
        enable_prompt_pattern: Regular expression for control view prompts.
    
    """
    
    # Prompt patterns for DPtech devices
    # Matches both user view: <hostname> and control view: [hostname]
    prompt_pattern = r"<[^>]+>|\[[^\]]+\]"
    
    # Control view (privileged mode) prompt pattern
    enable_prompt_pattern = r"\[[^\]]+\]"
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize DPtech connection with ANSI escape code support."""
        super().__init__(*args, **kwargs)
        self.ansi_escape_codes = True
    
    def session_preparation(self) -> None:
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
        pri_prompt_terminator: str = ">"
        alt_prompt_terminator: str = "]"
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
        cmd: str = "control",
        **kwargs: Any,
    ) -> str:
        """
        Enter control view (privileged mode) on DPtech devices.
        
        The control view provides elevated privileges similar to
        Cisco's enable mode. In this view, users can execute
        configuration commands and view sensitive information.
        """
        return super().enable(cmd=cmd, **kwargs)

    def check_enable_mode(self, check_string: str = "]") -> bool:
        return super().enable(cmd=cmd)

    def exit_enable_mode(self, exit_command: str = "quit") -> str:   
        return super.exit_enable_mode(exit_command=exit_command)

    def config_mode(
        self,
        config_command: str = "system",
        pattern: str = r"config",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "quit", pattern: str = r"]") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string: str = "config", pattern: str = "", force_regex: bool = False) -> bool:
        return super().check_config_mode(exit_config=exit_config, pattern=pattern)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        **kwargs: Any
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            **kwargs
        )

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
