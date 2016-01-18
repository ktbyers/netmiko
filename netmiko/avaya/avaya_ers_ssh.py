'''
Netmiko support for Avaya Ethernet Routing Switch
'''
from __future__ import print_function
from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER
import time

# Avaya presents Enter Ctrl-Y to begin.
CTRL_Y = '\x19'


class AvayaErsSSH(SSHConnection):
    '''
    Netmiko support for Avaya Ethernet Routing Switch
    '''
    def special_login_handler(self, delay_factor=.5):
        '''
        Avaya ERS presents the following as part of the login process:

        Enter Ctrl-Y to begin.
        '''
        delay_factor = self.select_delay_factor(delay_factor)

        # Handle 'Enter Ctrl-Y to begin'
        i = 0
        while i <= 12:
            if self.remote_conn.recv_ready():
                output = self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if 'Ctrl-Y' in output:
                    self.remote_conn.sendall(CTRL_Y)
                if 'sername' in output:
                    self.remote_conn.sendall(self.username + '\n')
                elif 'ssword' in output:
                    self.remote_conn.sendall(self.password + '\n')
                    break
                time.sleep(delay_factor)
            else:
                self.remote_conn.sendall('\n')
                time.sleep(2 * delay_factor)
            i += 1
