from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkEOLT9702Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.config_mode(config_command="config")
        self.send_command("vty output show-all")
        self.exit_config_mode(exit_config="exit")
        self.exit_enable_mode(exit_command="exit")


class OptilinkEOLT9702Telnet(OptilinkEOLT9702Base):
    """Optilink EOLT 97028P2AB telnet driver"""

    pass
