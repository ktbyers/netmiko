from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER
import time

class CiscoAsaSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        ASA must go into enable mode to disable_paging
        '''

        self.enable()
        self.disable_paging(command="terminal pager 0\n")
        self.set_base_prompt()


    def enable(self, delay_factor=.5):
        '''
        Enter enable mode

        Must manually control the channel at this point for ASA
        '''

        self.clear_buffer()
        self.remote_conn.send("\nenable\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        if 'assword' in output:
            self.remote_conn.send(self.secret+'\n')
            self.remote_conn.send('\n')
            time.sleep(1*delay_factor)
            output += self.remote_conn.recv(MAX_BUFFER)

        self.set_base_prompt()
        self.clear_buffer()
