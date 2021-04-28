"""Subclass specific to Cisco Viptela."""
import time

from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoViptelaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco Viptela."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="paginate false")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=")#", pattern="#"):
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, cmd="commit", confirm=False, confirm_response=""):
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def config_mode(self, config_command="conf terminal", pattern=""):
        """
        Enter into configuration mode on remote device.
        """
        return super().config_mode(config_command=config_command, pattern=pattern)

    def exit_config_mode(self, exit_config="end", pattern="#"):
        """Exit from configuration mode."""
        # Viptela requires committing before exiting config mode.
        self.save_config()
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)
