'''
Avaya Virtual Services Platform Support
'''
from __future__ import print_function
from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection

class AvayaVspSSH(SSHConnection):
    '''
    Avaya Virtual Services Platform Support
    '''
    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''
        self.disable_paging(command="terminal more disable\n")
        self.set_base_prompt()

