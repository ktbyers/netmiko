from netmiko.no_enable import NoEnable
from netmiko.cisco_base_connection import CiscoBaseConnection


class HillstoneStoneosBase(NoEnable, CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"#")
        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def save_config(
        self, cmd: str = "save all", confirm: bool = True, confirm_response: str = "y"
    ) -> str:
        """Saves Config Using Copy Run Start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class HillstoneStoneosSSH(HillstoneStoneosBase):
    pass
