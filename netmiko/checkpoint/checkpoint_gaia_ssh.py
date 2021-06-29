from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection


class CheckPointGaiaSSH(NoConfig, BaseConnection):
    """
    Implements methods for communicating with Check Point Gaia
    firewalls.
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Set the base prompt for interaction ('>').
        """
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="set clienv rows 0")

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        raise NotImplementedError
