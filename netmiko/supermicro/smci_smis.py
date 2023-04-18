from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.no_enable import NoEnable
import time


class SmciSwitchSmisBase(NoEnable, CiscoBaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.config_mode()
        self.disable_paging(command="set cli pagination off")
        self.set_terminal_width(command="terminal width 511")
        self.exit_config_mode()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def save_config(
        self,
        cmd: str = "write startup-config",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Save config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class SmciSwitchSmisSSH(SmciSwitchSmisBase):
    pass


class SmciSwitchSmisTelnet(SmciSwitchSmisBase):
    pass
