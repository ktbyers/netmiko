from netmiko.cisco_base_connection import CiscoBaseConnection
import time


class InfineraBase(CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging("terminal more off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()


class InfineraPacketSSH(InfineraBase):
    pass


class InfineraPacketTelnet(InfineraBase):
    pass
