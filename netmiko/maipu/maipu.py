import time

from netmiko.cisco_base_connection import CiscoBaseConnection


class MaipuBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="more off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(
        self, cmd: str = "write", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config Using Copy Run Start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class MaipuSSH(MaipuBase):
    """MAIPU SSH driver"""

    pass


class MaipuTelnet(MaipuBase):
    """MAIPU telnet driver"""

    pass
