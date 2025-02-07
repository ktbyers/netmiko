from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoBaseConnection


class BintecBossBase(NoEnable, NoConfig, CiscoBaseConnection):
    """Support for BinTec/Funkwerk (BOSS) devices"""

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r">")
        self.set_base_prompt()

    def save_config(
        self,
        cmd: str = "cmd=save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save Config to flash."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def _reload_device(
        self,
        cmd: str = "cmd=reboot",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Reloads the device."""
        return self._send_command_timing_str(command_string=cmd)


class BintecBossSSH(BintecBossBase):
    pass


class BintecBossTelnet(BintecBossBase):
    pass
