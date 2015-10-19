'''
Netmiko Ruckus ZoneDirector support
'''
from __future__ import print_function
from __future__ import unicode_literals
import time

from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

class zdSSH(SSHConnection):
    '''
    Netmiko Ruckus ZoneDirector support
    '''
    def special_login_handler(self, delay_factor=.3):
        '''
        ZoneDirector presents with the following on login (in certain OS versions)

        Please login: username
        Password:****
        '''
        i = 0
        while i <= 12:
            if self.remote_conn.recv_ready():
                output = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
                if 'Please login' in output or 'User' in output:
                    self.remote_conn.sendall(self.username + '\n')
                elif 'Password' in output:
                    self.remote_conn.sendall(self.password + '\n')
                    break
                time.sleep(delay_factor)
            else:
                self.remote_conn.sendall('\n')
                time.sleep(delay_factor*3)
            i += 1
    def enable(self):
        '''
        need force in case previous user is active.
        '''

        debug = False

        output = self.send_command('enable force')

        if debug:
            print(output)

        self.set_base_prompt()
        self.clear_buffer()

    def config_mode(self, config_command='config'):
        '''
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''

        # Call parent class with specific command for entering config mode
        return super(zdSSH, self).config_mode(config_command=config_command)
