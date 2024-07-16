from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkGOLT92416Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()


class OptilinkGOLT92416Telnet(OptilinkGOLT92416Base):
    """Optilink EOLT 97028P2AB telnet driver"""

    pass
