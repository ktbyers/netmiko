from netmiko.cisco_base_connection import CiscoSSHConnection


class LancomLCOSSX5SSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        The connection will enter `Privileged EXEC` by default, as the `EXEC` mode
        offers inconsistent command options
        """
        self._test_channel_read()
        self.enable(enable_pattern=r"#")
        self.set_base_prompt()
        self.disable_paging()
        self.clear_buffer()

    def check_config_mode(
        self,
        check_string: str = "(Config)#",
        pattern: str = "#",
        force_regex: bool = False,
    ) -> bool:
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_enable_mode(self, exit_command: str = "end") -> str:
        """Exits enable (privileged exec) mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def cleanup(self, command: str = "logout") -> None:
        """Cleanup / Gracefully exit the SSH session."""
        if self.check_config_mode():
            self.exit_config_mode()
        return super().cleanup(command=command)

    def save_config(
        self,
        cmd: str = "write memory confirm",
        confirm: bool = False,
        confirm_response: str = "y",
    ) -> str:
        """Save the running configuration to memory."""
        if self.check_config_mode():
            self.exit_config_mode()
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )
