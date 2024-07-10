from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection


class VertivMPHBase(NoEnable, NoConfig, CiscoSSHConnection):
    """
    Support for Vertiv MPH Power Distribution Units.
    Should work with any Vertiv Device with an RPC2 module.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        # self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"cli->")
        self.set_base_prompt()

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def cleanup(self, command: str = "logout") -> None:
        return super().cleanup(command=command)


class VertivMPHSSH(VertivMPHBase):
    pass
