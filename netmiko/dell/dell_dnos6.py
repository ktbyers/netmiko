"""Dell N2/3/4000 base driver- supports DNOS6."""
from __future__ import unicode_literals
from netmiko.dell.dell_powerconnect import DellPowerConnectBase
import time


class DellDNOS6Base(DellPowerConnectBase):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal length 0")
        self.set_terminal_width()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='copy running-configuration startup-configuration', confirm=False):
        """Saves Config"""
        return super(DellDNOS6SSH, self).save_config(cmd=cmd, confirm=confirm)


class DellDNOS6SSH(DellDNOS6Base):
    pass


class DellDNOS6Telnet(DellDNOS6Base):
    pass
