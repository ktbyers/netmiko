from __future__ import unicode_literals
from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
import time
import re


class DlinkDSBase(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(self, *args, **kwargs):
        """No implemented enable mode on D-Link yet"""
        pass

    def check_enable_mode(self, *args, **kwargs):
        """No implemented enable mode on D-Link yet"""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No implemented enable mode on D-Link yet"""
        pass

    def check_config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        pass

    def config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        return ""

    def exit_config_mode(self, *args, **kwargs):
        """No config mode on D-Link"""
        return ""

    def save_config(self, cmd="save", confirm=False):
        """Saves configuration."""
        log.debug("Saving all configurations to NV-RAM")
        return self.send_command_timing("save")

    def cleanup(self):
        """Return paging before disconnect"""
        self.send_command_timing("enable clipaging")
        log.debug("Exiting disable_paging")

    def strip_command(self, command_string, output):
        return re.sub(r"^.*?[\r\n]+Command:.*?[\n\r]+", "", output)


class DlinkDSSSH(DlinkDSBase):
    pass


class DlinkDSTelnet(DlinkDSBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\n" if default_enter is None else default_enter
        super(DlinkDSTelnet, self).__init__(*args, **kwargs)
