from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkEOLT1144Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        self.clear_buffer()
        self.exit_enable_mode()


class OptilinkEOLT1144Telnet(OptilinkEOLT1144Base):
    """Optilink EOLT 1144 telnet driver"""

    pass
