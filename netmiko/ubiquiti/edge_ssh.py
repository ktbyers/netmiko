from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class UbiquitiEdgeSSH(CiscoSSHConnection):
    """
    Implements support for Ubiquity Edge devices.

    Mostly conforms to Cisco IOS style syntax with a few minor changes.
    """
    def check_config_mode(self, check_string=')#'):
        """Checks if the device is in configuration mode or not."""
        return super(UbiquitiEdgeSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(UbiquitiEdgeSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='exit'):
        """Exit configuration mode."""
        return super(UbiquitiEdgeSSH, self).exit_config_mode(exit_config=exit_config)

    def exit_enable_mode(self, exit_command='exit'):
        """Exit enable mode."""
        return super(UbiquitiEdgeSSH, self).exit_enable_mode(exit_command=exit_command)
