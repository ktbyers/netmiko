from netmiko.cisco_base_connection import CiscoBaseConnection


class GenexisSOLT33Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.config_mode()
        cmd = "line width 256"
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging(command="screen-rows per-page 0")
        self.clear_buffer()
        self.exit_config_mode()
        self.exit_enable_mode()

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            self.read_until_pattern(pattern=exit_command)
            output += self.read_until_pattern(pattern=r">")
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output


class GenexisSOLT33Telnet(GenexisSOLT33Base):
    """Genexis SOLT33 telnet driver"""

    pass
