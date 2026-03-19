"""
DPtech (DeepInfo) Network Devices SSH and Telnet Driver for Netmiko.

This module provides support for DPtech (also known as DeepInfo) firewalls
and network devices. DPtech devices use a hierarchical view system similar to
Huawei, with different prompt formats for various operational modes.

Supported Views and Prompt Formats:
    - User View (普通视图): <hostname>
    - Control View (控制视图): [hostname] - privileged mode
    - Configuration Mode (配置模式): [hostname-config] - system configuration

Usage Example:
    >>> from netmiko import ConnectHandler
    >>> device = {
    ...     "device_type": "dptech",
    ...     "host": "192.168.1.1",
    ...     "username": "admin",
    ...     "password": "password",
    ... }
    >>> with ConnectHandler(**device) as conn:
    ...     conn.enable()
    ...     output = conn.send_command("show version")
    ...     conn.send_config_set(["sys", "firewall policy id 1"])

Supported Features:
    - SSH and Telnet connectivity
    - Automatic prompt detection (<hostname> and [hostname])
    - Enable/Disable paging (terminal line 0)
    - Control view (privileged mode) management
    - Configuration mode (sys)
    - Save configuration
    - ANSI escape code handling
    - Session cleanup

Author: Netmiko Community
License: MIT
"""

import re
import time
from typing import Optional, Any

from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable


class DpTechBase(NoEnable, BaseConnection):
    """
    Base connection class for DPtech (DeepInfo) network devices.
    
    This class implements device-specific handling for DPtech firewalls
    and network equipment, including prompt pattern recognition, view
    management, and configuration operations.
    
    Attributes:
        prompt_pattern: Regular expression matching DPtech prompts in both
            user view (<hostname>) and control view ([hostname]).
        pri_prompt_terminator: Primary prompt terminator character (<).
        alt_prompt_terminator: Alternate prompt terminator character (>).
        enable_prompt_pattern: Regular expression for control view prompts.
    
    Example:
        >>> conn = DpTechSSH(**device_params)
        >>> conn.enable()
        >>> conn.send_command("show version")
    """
    
    # Prompt patterns for DPtech devices
    # Matches both user view: <hostname> and control view: [hostname]
    prompt_pattern = r"<[^>]+>|\[[^\]]+\]"
    
    # User view (normal mode) prompt terminators
    pri_prompt_terminator = "<"
    alt_prompt_terminator = ">"
    
    # Control view (privileged mode) prompt pattern
    enable_prompt_pattern = r"\[[^\]]+\]"
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize DPtech connection with ANSI escape code support."""
        super().__init__(*args, **kwargs)
        self.ansi_escape_codes = True
    
    def session_preparation(self) -> None:
        """
        Prepare the session after SSH/Telnet connection is established.
        
        This method is automatically called during connection initialization.
        It performs the following:
            1. Enable ANSI escape code processing
            2. Detect and set the device prompt
            3. Disable paging (terminal line 0)
            4. Set terminal width to 511 columns
            5. Clear any remaining buffer data
        """
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command="screen-width 511", pattern=r"screen-width")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command: str = "terminal line 0", delay_factor: float = 1) -> str:
        """
        Disable command output paging on DPtech devices.
        
        Args:
            command: The command to disable paging (default: "terminal line 0")
            delay_factor: Delay factor for command execution
        
        Returns:
            Command output from the device
        """
        return super().disable_paging(command=command, delay_factor=delay_factor)

    def set_base_prompt(
        self,
        pri_prompt_terminator: Optional[str] = None,
        alt_prompt_terminator: Optional[str] = None,
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Set the base prompt for DPtech devices.
        
        DPtech devices use <hostname> in user view and [hostname] in 
        control view. This method extracts and stores the hostname portion.
        
        Args:
            pri_prompt_terminator: Primary prompt terminator (default: <)
            alt_prompt_terminator: Alternate prompt terminator (default: >)
            delay_factor: Delay factor for prompt detection
            pattern: Optional custom regex pattern for prompt matching
        
        Returns:
            The detected prompt string
        """
        # Use class defaults if not specified
        if pri_prompt_terminator is None:
            pri_prompt_terminator = self.pri_prompt_terminator
        if alt_prompt_terminator is None:
            alt_prompt_terminator = self.alt_prompt_terminator
            
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
        pattern: str = "control view",
        re_flags: int = 0,
    ) -> str:
        """
        Enter control view (privileged mode) on DPtech devices.
        
        The control view provides elevated privileges similar to
        Cisco's enable mode. In this view, users can execute
        configuration commands and view sensitive information.
        
        Args:
            cmd: Command to enter control view (default: "c")
            pattern: Pattern to expect after command execution
            re_flags: Regular expression flags
        
        Returns:
            Command output including any status messages
        """
        output = self.send_command_timing(cmd, strip_prompt=False, strip_command=False)
        if "control" in output.lower() and "view" in output.lower():
            return output
        return output

    def check_enable_mode(self, *args: Any, **kwargs: Any) -> bool:
        """
        Check if the session is in control view (privileged mode).
        
        Returns:
            True if in control view (prompt starts with [), False otherwise
        """
        output = self.send_command_timing("\n", strip_prompt=False, strip_command=False)
        return "control view" in output.lower() or output.strip().startswith("[")

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """
        Exit control view and return to user view.
        
        Returns:
            Command output from the device
        """
        return self.send_command("quit", *args, **kwargs)

    def config_mode(
        self,
        config_command: str = "sys",
        pattern: str = r"\[",
        re_flags: int = 0,
    ) -> str:
        """
        Enter system configuration mode.
        
        Args:
            config_command: Command to enter config mode (default: "sys")
            pattern: Pattern to expect after entering config mode
            re_flags: Regular expression flags
        
        Returns:
            Command output from the device
        """
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "quit", pattern: Optional[str] = None) -> str:
        """
        Exit configuration mode.
        
        Returns to control view (if in config mode) or user view
        (if in control view).
        
        Args:
            exit_config: Command to exit config mode (default: "quit")
            pattern: Optional pattern to match after exit
        
        Returns:
            Command output from the device
        """
        if pattern is None:
            # Match control view [hostname] or user view <hostname>
            pattern = r"(?:\[|<)"
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(self, check_string: str = "[", pattern: str = "", force_regex: bool = False) -> bool:
        """
        Check if the session is in configuration mode.
        
        Args:
            check_string: String to check for in prompt
            pattern: Optional regex pattern
            force_regex: Force regex matching
        
        Returns:
            True if in configuration mode, False otherwise
        """
        output = self.send_command_timing("\n", strip_prompt=False, strip_command=False)
        return output.strip().startswith("[")

    def send_config_set(
        self,
        config_commands: Any = None,
        exit_config_mode: bool = True,
        **kwargs: Any
    ) -> str:
        """
        Send configuration commands to the device.
        
        This method automatically enters control view before applying
        configuration commands.
        
        Args:
            config_commands: List or iterator of configuration commands
            exit_config_mode: Whether to exit config mode after commands
        
        Returns:
            Combined output from all configuration commands
        """
        if config_commands is None:
            return ""
        
        # Ensure we are in control view before configuration
        self.enable()
        
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
        try:
            if pattern is None:
                pattern = self.prompt_pattern
            prompt = super().find_prompt(delay_factor=delay_factor, pattern=pattern)
        except Exception:
            # Fallback to default detection if pattern fails
            prompt = super().find_prompt(delay_factor=delay_factor)
        
        return prompt.strip()

    def save_config(
        self,
        cmd: str = "save",
        confirm: bool = True,
        confirm_response: str = "y",
        read_timeout: float = 100.0,
    ) -> str:
        """
        Save the running configuration to startup configuration.
        
        Args:
            cmd: Save command (default: "save")
            confirm: Whether to confirm the save operation
            confirm_response: Confirmation response (default: "y")
            read_timeout: Timeout for command execution
        
        Returns:
            Command output including save status messages
        """
        # Ensure we are in control view before saving
        self.enable()
        
        if confirm:
            pattern = rf"(?:[Cc]ontinue\?|{self.prompt_pattern})"
            output = self._send_command_str(
                command_string=cmd,
                expect_string=pattern,
                strip_prompt=False,
                strip_command=False,
                read_timeout=read_timeout,
            )
            if confirm_response and re.search(r"[Cc]ontinue\?", output):
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
        """
        Clean up the session before closing.
        
        Args:
            command: Command to execute before disconnecting
        """
        return super().cleanup(command=command)


class DpTechSSH(DpTechBase):
    """
    SSH driver for DPtech (DeepInfo) network devices.
    
    This class extends DpTechBase to provide SSH-specific functionality.
    Use device_type="dptech" with ConnectHandler to use this driver.
    
    Example:
        >>> device = {
        ...     "device_type": "dptech",
        ...     "host": "192.168.1.1",
        ...     "username": "admin",
        ...     "password": "password",
        ... }
        >>> with ConnectHandler(**device) as conn:
        ...     print(conn.find_prompt())
    """
    pass


class DpTechTelnet(DpTechBase):
    """
    Telnet driver for DPtech (DeepInfo) network devices.
    
    This class extends DpTechBase to provide Telnet-specific functionality.
    Use device_type="dptech_telnet" with ConnectHandler to use this driver.
    
    Example:
        >>> device = {
        ...     "device_type": "dptech_telnet",
        ...     "host": "192.168.1.1",
        ...     "username": "admin",
        ...     "password": "password",
        ... }
        >>> with ConnectHandler(**device) as conn:
        ...     print(conn.find_prompt())
    """
    pass
