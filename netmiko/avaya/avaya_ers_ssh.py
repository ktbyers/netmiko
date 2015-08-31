from __future__ import print_function
from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection

class AvayaErsSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''

        # Setup commands for logging into switch
        ctrl_y_command = '\x19'

        self.remote_conn.sendall(ctrl_y_command)

        self.disable_paging()
        self.set_base_prompt()