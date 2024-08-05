import time
from netmiko.cisco_base_connection import CiscoBaseConnection


class OptilinkGOLT92416Base(CiscoBaseConnection):
    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            self.read_until_pattern(pattern=exit_command)
            output += self.read_until_pattern(pattern=r"gpon>")
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        print("exit_enable_mode")
        print(self.find_prompt())
        return output


class OptilinkGOLT92416Telnet(OptilinkGOLT92416Base):
    """Optilink EOLT 97028P2AB telnet driver"""

    pass
