from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko import log
import time

class DlinkBase(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(self, *args, **kwargs):
        """No enable mode on D-Link"""
        pass

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on D-Link"""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on D-Link"""
        pass

    def check_config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        pass

    def config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        return ''

    def exit_config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        return ''

    def save_config(self, cmd='save', confirm=False):
        """Saves configuration."""
        return super(DlinkBase, self).save_config(cmd=cmd, confirm=confirm)

class DlinkSSH(DlinkBase):
    pass

class DlinkTelnet(DlinkBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\n' if default_enter is None else default_enter
        super(DlinkTelnet, self).__init__(*args, **kwargs)
