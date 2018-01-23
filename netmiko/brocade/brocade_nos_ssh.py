"""Support for Brocade NOS/VDX."""
from __future__ import unicode_literals
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
        self.write_channel(self.RETURN)
        time.sleep(1 * delay_factor)

    def save_config(self):
        """Save Config for Brocade VDX."""
        output = self.send_command('copy running-config startup-config', '[Y/N]')
        output += self.send_command('y')
        return output