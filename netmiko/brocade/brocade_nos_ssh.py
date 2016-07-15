"""Support for Brocade NOS/VDX."""
import time
from netmiko.ssh_connection import SSHConnection


class BrocadeNosSSH(SSHConnection):
    """Support for Brocade NOS/VDX."""
    def enable(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass

    def special_login_handler(self, delay_factor=.5):
        '''
            Adding a delay after login
        '''
        delay_factor = self.select_delay_factor(delay_factor)
        self.remote_conn.sendall('\n')
        time.sleep(2 * delay_factor)
