from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkEOLT1144Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        self.clear_buffer()
        self.exit_enable_mode()
        
    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )


class OptilinkEOLT1144Telnet(OptilinkEOLT1144Base):
    """Optilink EOLT 1144 telnet driver"""

    pass
