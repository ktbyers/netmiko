"""Adva F3 Device Support"""
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=abstract-method
# pylint: disable=arguments-differ
from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from typing import (
    Optional,
    Sequence,
    TextIO,
    Union,
    Any,
)

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class AdvaAosFsp150f3SSH(NoEnable, NoConfig, CiscoSSHConnection):
    """
       Adva AOS FSP 15P F3 SSH Base Class
       F3 AOS applies for the following FSP150 device types
       FSP150CC-XG21x
       FSP150CC-GE11x
       FSP150CC-GE20x
       These devices don't have a Enable Mode or Config Mode
       Configuration Should be applied via the configuration context
        home
        configure communication
        add ip-route nexthop xxxxxxx

        #
        #CLI:PORT N2A SHAPER-1-1-1-3-0  Create
        #
        home
        network-element ne-1

        Use of home to return to CLI root context

    Args:
        CiscoSSHConnection (class): Netmiko Cisco SSH Connection Class
        NoEnable (class): Netmiko NoEnable Class
        NoConfig (class): Netmiko NoConfig Class
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Adva F3 Device Instantiation
        \n for default enter causes some issues with the Adva
        so setting to \r
        """
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"

        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.
        Handles devices with security prompt enabled
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        data = self._test_channel_read(
            pattern=r"Do you wish to continue \[Y\|N\]-->|-->"
        )
        if "continue" in data:
            self.write_channel(f"y{self.RETURN}")
        else:
            self.write_channel(f"home{self.RETURN}")
        time.sleep(0.33 * delay_factor)
        self._test_channel_read(pattern=r"-->")
        self.set_base_prompt()
        self.disable_paging(cmd_verify=False)
        self.clear_buffer()

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Method to disable paging on the Adva, multi-line configuration command required

        Args:
            command (str, optional): Command to Disable Paging. Defaults to "terminal length 0".
            delay_factor (Optional[float], optional): Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5. Defaults to None.
            cmd_verify (bool, optional): Verify command echo before proceeding. Defaults to True.
            pattern (Optional[str], optional): Regular expression pattern used to identify that reading is done. Defaults to None.

        Returns:
            str: SSH Channel Output
        """
        # Multiline Command Below is used for paging
        command = (
            "configure user-security"
            + self.TELNET_RETURN
            + "config-user "
            + self.username
            + " cli-paging disabled"
            + self.TELNET_RETURN
            + "home"
            + self.TELNET_RETURN
        )
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without > or #).

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt

        :param delay_factor: See __init__: global_delay_factor

        :param pattern: Regular expression pattern to search for in find_prompt() call
        """
        prompt = self.find_prompt()
        match = re.search(r"(^.+?)-->$", prompt)
        if not match:
            raise ValueError("Router prompt not found: {0}".format(repr(prompt)))
        self.base_prompt = match[1]
        return self.base_prompt

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], TextIO, None] = None,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = 2.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"#",
        bypass_commands: Optional[
            str
        ] = r"(add\s+\w+\s+[A-Za-z0-9#\?!@\$%\^&\*-]*\s+[A-Za-z0-9#\?!@\$%\^&\*-]*\s+(superuser|crypto|maintenance|provisioning|retrieve|test-user)|secret.*)",
    ) -> str:
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.

        Args:
            config_commands (Union[str, Sequence[str], TextIO, None], optional): _description_. Defaults to None.
            exit_config_mode (bool, optional): _description_. Defaults to True.
            read_timeout (Optional[float], optional): _description_. Defaults to 2.0.
            delay_factor (Optional[float], optional): _description_. Defaults to None.
            max_loops (Optional[int], optional): _description_. Defaults to None.
            strip_prompt (bool, optional): _description_. Defaults to False.
            strip_command (bool, optional): _description_. Defaults to False.
            config_mode_command (Optional[str], optional): _description_. Defaults to None.
            cmd_verify (bool, optional): _description_. Defaults to True.
            enter_config_mode (bool, optional): _description_. Defaults to True.
            error_pattern (str, optional): _description_. Defaults to "".
            terminator (str, optional): _description_. Defaults to r"#".
            bypass_commands (Optional[str], optional): _description_. Defaults to r"(add.*|secret.*)".

        Returns:
            str: SSH Channel Output
        """
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
