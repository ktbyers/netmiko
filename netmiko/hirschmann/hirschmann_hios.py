"""
Tested with Hirschmann BRS20 (Bobcat Rail Switch) running HiOS.
"""

from netmiko.cisco_base_connection import CiscoBaseConnection


class HirschmannHiOSBase(CiscoBaseConnection):
    """Base class for Hirschmann HiOS devices."""

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="cli numlines 0")

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Save the configuration."""
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)


class HirschmannHiOSSSH(HirschmannHiOSBase):
    """Hirschmann HiOS SSH driver."""

    pass
