from __future__ import print_function
from __future__ import unicode_literals
import re
import time
from netmiko.ssh_connection import SSHConnection


class HPProcurveSSH(SSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established"""
        # HP uses - 'Press any key to continue'
        time.sleep(1)
        self.remote_conn.sendall("\n")
        time.sleep(1)

        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        self.set_base_prompt()
        self.disable_paging(command="\nno page\n")

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE,
               default_username='manager'):
        """Enter enable mode"""
        debug = False
        output = self.send_command(cmd)
        if 'username' in output.lower():
            output += self.send_command(default_username)
        if 'password' in output.lower():
            output += self.send_command(self.secret)
        if debug:
            print(output)
        self.clear_buffer()
        return output
