'''
Netmiko Cisco WLC support
'''
from __future__ import print_function
from __future__ import unicode_literals
import time

from netmiko.ssh_connection import BaseSSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

class CiscoWlcSSH(BaseSSHConnection):
    '''
    Netmiko Cisco WLC support
    '''
    def special_login_handler(self, delay_factor=.3):
        '''
        WLC presents with the following on login (in certain OS versions)

        login as: user

        (Cisco Controller)

        User: user

        Password:****
        '''
        i = 0
        while i <= 12:
            if self.remote_conn.recv_ready():
                output = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
                if 'login as' in output or 'User' in output:
                    self.remote_conn.sendall(self.username + '\n')
                elif 'Password' in output:
                    self.remote_conn.sendall(self.password + '\n')
                    break
                time.sleep(delay_factor)
            else:
                self.remote_conn.sendall('\n')
                time.sleep(delay_factor*3)
            i += 1


    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        Cisco WLC uses "config paging disable" to disable paging
        '''

        self.disable_paging(command="config paging disable\n")
        self.set_base_prompt()


    def cleanup(self):
        '''
        Reset WLC back to normal paging
        '''

        self.send_command("config paging enable\n")

