from netmiko.cisco_base_connection import CiscoSSHConnection


class BroadcomIcosSSH(CiscoSSHConnection):
    """
    Implements support for Broadcom Icos devices.
    Syntax its almost identical to Cisco IOS in most cases
    """

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config)

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit enable mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
