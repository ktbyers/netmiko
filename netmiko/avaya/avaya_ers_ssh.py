"""Netmiko support for Avaya Ethernet Routing Switch."""
from __future__ import print_function
from __future__ import unicode_literals

import re
import time

from netmiko.cisco_base_connection import CiscoSSHConnection

# Avaya presents Enter Ctrl-Y to begin.
CTRL_Y = '\x19'


class AvayaErsSSH(CiscoSSHConnection):
    """Netmiko support for Avaya Ethernet Routing Switch."""

    def config_mode(self, config_command='config term', pattern=''):
        """

        Enter into configuration mode on remote device.

        Avaya ERS devices can have a prompt longer than 20 characters in
        config mode.
        """
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super(CiscoSSHConnection, self).config_mode(config_command=config_command,
                                                            pattern=pattern)    
    def check_config_mode(self, check_string='#', pattern=''):
            """

            Checks if the device is in configuration mode or not.
            
            Avaya ERS devices can have a prompt longer than 20 characters in
            config mode.
            """
            if not pattern:
                pattern = re.escape(self.base_prompt)
            return super(CiscoSSHConnection, self).check_config_mode(check_string=check_string,
                                                                      pattern=pattern)    
    def special_login_handler(self, delay_factor=1):
        """
        Avaya ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin.

        Some Avaya ERS devices present a menu interface upon login
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Handle 'Enter Ctrl-Y to begin' and Menu if present
        output = ""
        i = 0
        while i <= 6:
            output = self.read_channel()
            if output:
                if 'Ctrl-Y' in output:
                    self.write_channel(CTRL_Y)
                if 'sername' in output:
                    self.write_channel(self.username + self.RETURN)
                if 'ssword' in output:
                    self.write_channel(self.password + self.RETURN)
                if "Menu" in output:
                    self.write_channel('c')
                    break
                time.sleep(.5 * delay_factor)
            else:
                self.write_channel(self.RETURN)
                time.sleep(1 * delay_factor)
            i += 1
