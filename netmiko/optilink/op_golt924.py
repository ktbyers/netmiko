from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkGOLT924Base(CiscoBaseConnection):
    """
    Optilink GOLT 92408A
    Optilink GOLT 92408A16A
    """

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """Exit from enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            self.read_until_pattern(pattern=exit_command)
            output += self.read_until_pattern(pattern=r"gpon>")
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output


class OptilinkGOLT924Telnet(OptilinkGOLT924Base):
    """
    Optilink GOLT 92416A telnet driver
    Optilink GOLT 92408A telnet driver
    """

    pass
