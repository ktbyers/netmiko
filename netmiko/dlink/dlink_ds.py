from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection
import time


class DlinkDSBase(NoEnable, NoConfig, CiscoSSHConnection):
    """Supports D-Link DGS/DES device series (there are some DGS/DES devices that are web-only)"""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command="disable clipaging"):
        return super().disable_paging(command=command)

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def cleanup(self):
        """Return paging before disconnect"""
        self.send_command_timing("enable clipaging")
        return super().cleanup()


class DlinkDSSSH(DlinkDSBase):
    pass


class DlinkDSTelnet(DlinkDSBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
