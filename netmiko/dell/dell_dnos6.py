"""Dell N2/3/4000 base driver- supports DNOS6."""

from netmiko.dell.dell_powerconnect import DellPowerConnectBase


class DellDNOS6Base(DellPowerConnectBase):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.set_terminal_width()
        self.disable_paging(command="terminal length 0")

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


class DellDNOS6SSH(DellDNOS6Base):
    pass


class DellDNOS6Telnet(DellDNOS6Base):
    pass
