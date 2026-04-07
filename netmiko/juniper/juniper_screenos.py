from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class JuniperScreenOsSSH(NoEnable, NoConfig, BaseConnection):
    """
    Implement methods for interacting with Juniper ScreenOS devices.
    """

    def _try_session_preparation(self, force_data: bool = False) -> None:
        return super()._try_session_preparation(force_data=force_data)

    def session_preparation(self) -> None:
        """
        ScreenOS can be configured to require: Accept this agreement y/[n]
        """
        terminator = r"\->"
        pattern = rf"(?:Accept this.*|{terminator})"
        data = self.read_until_pattern(pattern=pattern)
        if "Accept this" in data:
            self.write_channel("y")
            data += self.read_until_pattern(pattern=terminator)
        self.set_base_prompt()
        self.disable_paging(command="set console page 0")

    def save_config(
        self,
        cmd: str = "save config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config."""
        return self._send_command_str(command_string=cmd)
