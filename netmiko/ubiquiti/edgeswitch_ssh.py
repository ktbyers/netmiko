from __future__ import unicode_literals

import re
import time

#from netmiko.base_connection import BaseConnection
from netmiko.cisco_base_connection import CiscoSSHConnection


class UbiquitiEdgeSwitchSSH(CiscoSSHConnection):
    """
    Implements support for Ubiquity EdgeSwitch devices.

    Passes on anything "enable" related as UBNT doesn't have this mode.
    """

    def check_config_mode(self, check_string=')#'):
        """Checks if the device is in configuration mode or not."""
        return super(UbiquitiEdgeSwitchSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(UbiquitiEdgeSwitchSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='exit'):
        """Exit configuration mode."""
       	return super(UbiquitiEdgeSwitchSSH, self).exit_config_mode(exit_config=exit_config)

    def exit_enable_mode(self, exit_command='exit'):
        return super(UbiquitiEdgeSwitchSSH, self).exit_enable_mode(exit_command=exit_command)


    def commit(self, confirm=False, confirm_delay=None, check=False, comment='',
               and_quit=False, delay_factor=1):
      
		return super(UbiquitiEdgeSwitchSSH, self).commit(confirm=False, confirm_delay=None, check=False, comment='',
               and_quit=False, delay_factor=1)

    def strip_prompt(self, *args, **kwargs):
        """Strip the trailing router prompt from the output."""
        return super(UbiquitiEdgeSwitchSSH, self).strip_prompt(*args, **kwargs)
