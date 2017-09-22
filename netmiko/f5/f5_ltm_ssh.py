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
        # Send disable paging cmd depends on F5 cli version
        cmd = self.dis_paging_cmd()
        self.disable_paging(command=cmd)
        time.sleep(1 * delay_factor)

    def dis_paging_cmd(self):
        """ return F5 disable_paging cli cmd """
        try:
            cli_cmd = 'show sys version | grep  -i version\n'
            version_res = self.send_command(str(cli_cmd))
            version = re.search(r'^\s+[Vv]ersion\s+(\d+).(\d+).(\d)', version_res, re.I | re.M)
            if version.group(1) in ['11', '12', '13']:
                return str("modify cli preference pager disabled\n")
            else: # version smaller then 10 send old cmd
                return str('set length 0\n')
        except Exception as e:
            raise ValueError("Can't find disable paging cli command")
            raise e

    def tmsh_mode(self, delay_factor=1):
        """tmsh command is equivalent to config command on F5."""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel("\ntmsh\n")
        time.sleep(1 * delay_factor)
        self.clear_buffer()
        return None

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove '\r's in the text."""
        newline = re.compile(r'(\r\n|\r\n\r\n|\r\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)
