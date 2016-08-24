"""Support for Brocade NOS/VDX."""
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeNosSSH(CiscoSSHConnection):
    """Support for Brocade NOS/VDX."""
    def enable(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Brocade VDX."""
        pass

    def special_login_handler(self, delay_factor=1):
        """Adding a delay after login."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.write_channel('\n')
        time.sleep(1 * delay_factor)
