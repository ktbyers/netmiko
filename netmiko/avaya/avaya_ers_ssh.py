"""Netmiko support for Avaya Ethernet Routing Switch."""
from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection

# Avaya presents Enter Ctrl-Y to begin.
CTRL_Y = '\x19'


class AvayaErsSSH(CiscoSSHConnection):
    """Netmiko support for Avaya Ethernet Routing Switch."""
    def special_login_handler(self, delay_factor=1):
        """
        Avaya ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin.
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Handle 'Enter Ctrl-Y to begin'
        output = ""
        i = 0
        while i <= 12:
            output = self.read_channel()
            if output:
                if 'Ctrl-Y' in output:
                    self.write_channel(CTRL_Y)
                if 'sername' in output:
                    self.write_channel(self.username + self.RETURN)
                elif 'ssword' in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(.5 * delay_factor)
            else:
                self.write_channel(self.RETURN)
                time.sleep(1 * delay_factor)
            i += 1

    def save_config(self, cmd='save config', confirm=False):
        """Save Config"""
        return super(AvayaErsSSH, self).save_config(cmd=cmd, confirm=confirm)
