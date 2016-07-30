import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class AristaSSH(CiscoSSHConnection):
    def special_login_handler(self, delay_factor=1):
        """
        Arista adds a "Last login: " message that doesn't always have sufficient time to be handled
        """
        time.sleep(3 * delay_factor)
        self.clear_buffer()
