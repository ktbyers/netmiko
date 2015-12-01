'''
Extreme support
'''
from netmiko.ssh_connection import SSHConnection


class ExtremeSSH(SSHConnection):
    '''
    Extreme support
    '''
    def session_preparation(self):
        '''
        Extreme requires enable mode to disable paging
        '''
        self.enable()
        self.disable_paging(command="disable clipaging\n")
        self.set_base_prompt()
