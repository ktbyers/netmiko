"""Aruba OS support"""
from netmiko.cisco_base_connection import CiscoSSHConnection


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""
    def session_preparation(self):
        """Aruba OS requires enable mode to disable paging."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no paging")

    def check_config_mode(self, check_string='(config) #', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
        if not pattern:
            pattern = self.base_prompt[:16]
        return super(ArubaSSH, self).check_config_mode(check_string=check_string,
                                                       pattern=pattern)
