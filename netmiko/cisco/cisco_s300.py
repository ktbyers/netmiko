from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoS300Base(CiscoSSHConnection):
    """
    Support for Cisco SG300 series of devices.

    Note, must configure the following to disable SG300 from prompting for username twice:

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


class CiscoS300SSH(CiscoS300Base):
    pass


class CiscoS300Telnet(CiscoS300Base):
    """
    Support for Cisco SG300 series of devices, with telnet.
    Note: can be used with Sx200 series, with telnet enabled.
    """

    pass
