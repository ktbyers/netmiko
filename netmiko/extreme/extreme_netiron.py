import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeNetironBase(CiscoSSHConnection):
    def save_config(self, cmd="write memory", confirm=False, confirm_response=""):
        """Save Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="skip-page-display")
        self.set_terminal_width()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()


class ExtremeNetironSSH(ExtremeNetironBase):
    pass


class ExtremeNetironTelnet(ExtremeNetironBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
