from typing import Any
from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoS500Base(CiscoBaseConnection):
    """
    Support for Cisco SG500 series of devices.

    Note, must configure the following to disable SG500 from prompting for username twice:

    configure terminal
    ip ssh password-auth
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.set_terminal_width(command="terminal width 511", pattern="terminal")
        self.disable_paging(command="terminal datadump")

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = True,
        confirm_response: str = "Y",
    ) -> str:
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CiscoS500SSH(CiscoS500Base):
    """
    Support for Cisco SG500 series of devices, with ssh.
    """

    pass


class CiscoS500Telnet(CiscoS500Base):
    """
    Support for Cisco SG500 series of devices, with telnet.
    """

    def __init__(self, **kwargs: Any) -> None:
        if "device_type" not in kwargs:
            kwargs["device_type"] = "cisco_s500_telnet"
        super().__init__(**kwargs)

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"User Name:",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet login. Can be username/password or just password.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt

        :param username_pattern: Pattern used to identify the username prompt

        :param pwd_pattern: Pattern used to identify the pwd prompt

        :param delay_factor: See __init__: global_delay_factor

        :param max_loops: Controls the wait time in conjunction with the delay_factor
        """
        return super().telnet_login(
            pri_prompt_terminator,
            alt_prompt_terminator,
            username_pattern,
            pwd_pattern,
            delay_factor,
            max_loops,
        )
