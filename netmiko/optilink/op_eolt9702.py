from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkEOLT9702Base(CiscoBaseConnection):
    """
    Optilink EOLT 9702-8P2AB
    Optilink EOLT 9702-4P
    """

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.config_mode()
        self.send_command("vty output show-all")
        self.exit_config_mode()
        self.exit_enable_mode()

    def config_mode(
        self,
        config_command: str = "config",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enter into configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit from enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            self.read_until_pattern(pattern=exit_command)
            output += self.read_until_pattern(pattern=r"OP_OLT>")
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#.*") -> str:
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)


class OptilinkEOLT9702Telnet(OptilinkEOLT9702Base):
    """
    Optilink EOLT 9702-8P2AB telnet driver
    Optilink EOLT 9702-4P telnet driver
    """

    pass
