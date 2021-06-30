"""Dell Force10 Driver - supports DNOS9."""
from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""

    def save_config(
        self,
        cmd: str = "copy running-configuration startup-configuration",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
