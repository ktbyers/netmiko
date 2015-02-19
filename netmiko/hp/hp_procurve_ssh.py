from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import time

class HPProcurveSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''

        # HP uses - 'Press any key to continue'
        time.sleep(1)
        self.remote_conn.send("\n")
        time.sleep(1)

        # HP output contains VT100 escape codes
        self.ansi_escape_codes = True

        self.disable_paging(command="\nno page\n")
        self.set_base_prompt()


    def enable(self, default_username='manager'):
        '''
        Enter enable mode
        '''

        DEBUG = False

        output = self.send_command('enable')
        if 'sername' in output:
            output += self.send_command(default_username)
        if 'assword' in output:
            output += self.send_command(self.secret)

        if DEBUG: 
            print output

        self.set_base_prompt()
        self.clear_buffer()

