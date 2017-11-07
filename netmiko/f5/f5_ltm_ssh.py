from __future__ import unicode_literals

import time
import re

from netmiko.base_connection import BaseConnection


class F5LtmSSH(BaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        self._test_channel_read()
        self.set_base_prompt()
        command = self.dis_paging_cmd()
        self.disable_paging(command=command)
        time.sleep(1 * delay_factor)
        self.tmsh_mode()
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def dis_paging_cmd(self):
        """ return F5 disable_paging cli cmd """
        try:
            cli_cmd = 'show sys version | grep  -i version\n'
            version_res = self.send_command(str(cli_cmd))
            version = re.search(r'^\s+[Vv]ersion\s+(\d+).(\d+).(\d)', version_res, re.I | re.M)
            if version.group(1) in ['11', '12', '13']:
                command = "{}modify cli preference pager disabled{}".format(self.RETURN, self.RETURN)
                return command
            else:
                command = "{}set length 0{}".format(self.RETURN, self.RETURN)
                return command
        except Exception as e:
            raise ValueError("Can't find disable paging cli command: " + e )

    def tmsh_mode(self, delay_factor=1):
        """tmsh command is equivalent to config command on F5."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        command = "{}tmsh{}".format(self.RETURN, self.RETURN)
        self.write_channel(command)
        time.sleep(1 * delay_factor)
        self.clear_buffer()
        return None
