import time
from netmiko.ssh_connection import SSHConnection


class AristaSSH(SSHConnection):
    def special_login_handler(self, delay_factor=1):
        """
        Arista adds a "Last login: " message that doesn't always have sufficient time to be handled
        """
        time.sleep(3 * delay_factor)
        self.clear_buffer()
