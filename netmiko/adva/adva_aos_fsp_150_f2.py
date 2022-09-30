"""Adva support."""
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=abstract-method
# pylint: disable=arguments-differ
from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from typing import Any, Optional
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class AdvaAosFsp150f2SSH(NoEnable, NoConfig, CiscoSSHConnection):
    """Adva AOS FSP 15P F2 SSH Base Class
       F2 AOS applies for the following FSP150 device types
       FSP150CC-825
       These devices don't have a Enable Mode or Config Mode
       Configuration Should be applied via the configuration context
        home
        configure snmp
        add v3user guytest noauth-nopriv
        home

        configure system
        home

        Use of home to return to CLI root context, home cannot be used from root
        LAB-R2-825-1:--> home
        Unrecognized command

    Args:
        CiscoSSHConnection (class): Netmiko Cisco SSH Connection Class
        NoEnable (class): Netmiko NoEnable Class
        NoConfig (class): Netmiko NoConfig Class
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Adva F2 Device Instantiation
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
            self.write_channel(f"help?{self.RETURN}")
        time.sleep(0.33 * delay_factor)
        self._test_channel_read(pattern=r"-->")
        self.set_base_prompt()
        self.clear_buffer()

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
        if not (match := re.search(r"(^.+?)([:].*)-->$", prompt)):
            raise ValueError("Router prompt not found: {0}".format(repr(prompt)))
            # Strip everything after first ':' from prompt
        self.base_prompt = match[1]
        return self.base_prompt
