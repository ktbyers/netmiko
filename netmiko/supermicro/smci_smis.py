from netmiko.cisco_base_connection import CiscoBaseConnection
import time


class SmciSwitchSmisBase(CiscoBaseConnection):
    def session_preparation(self):
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

    def check_enable_mode(self, check_string="#"):
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable(self, *args, **kwargs):
        """Supermicro switch does not support enable-mode command"""
        return ""

    def exit_enable_mode(self, *args, **kwargs):
        """Supermicro switch does not support enable-mode command"""
        return ""

    def save_config(
        self, cmd="write startup-config", confirm=False, confirm_response=""
    ):
        """Save config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class SmciSwitchSmisSSH(SmciSwitchSmisBase):
    pass


class SmciSwitchSmisTelnet(SmciSwitchSmisBase):
    pass
