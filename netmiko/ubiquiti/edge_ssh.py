import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class UbiquitiEdgeSSH(CiscoSSHConnection):
    """
    Implements support for Ubiquity EdgeSwitch devices.

    Mostly conforms to Cisco IOS style syntax with a few minor changes.

    This is NOT for EdgeRouter devices.
    """

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string: str = ")#", pattern: str = "") -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#.*") -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

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
