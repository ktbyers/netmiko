"""Dell PowerConnect Driver."""

from typing import Optional
from paramiko import SSHClient
import time
from netmiko.ssh_auth import SSHClient_noauth
from netmiko.cisco_base_connection import CiscoBaseConnection


class DellPowerConnectBase(CiscoBaseConnection):
    """Dell PowerConnect Driver."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal datadump")  # Dell 34xx
        self.disable_paging(command="terminal length 0")  # Dell 7xxx
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def check_config_mode(
        self,
        check_string: str = "(config)#",
        pattern: str = "",
        force_regex: bool = False,
    ) -> bool:
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "config", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )


class DellPowerConnectSSH(DellPowerConnectBase):
    """Dell PowerConnect Driver.

    To make it work, we have to override the SSHClient _auth method.
    If we use login/password, the ssh server use the (none) auth mechanism.
    """

    def _get_ssh_client_instance(self) -> SSHClient:
        """If not using SSH keys or agent, use noauth."""
        if not self.use_keys and not self.allow_agent:
            return SSHClient_noauth()
        return SSHClient()

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """
        Powerconnect presents with the following on login

        User Name:

        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "User Name:" in output:
                    assert isinstance(self.username, str)
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1


class DellPowerConnectTelnet(DellPowerConnectBase):
    """Dell PowerConnect Telnet Driver."""

    pass
