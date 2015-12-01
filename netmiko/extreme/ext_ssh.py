'''
EXT support
'''
from netmiko.ssh_connection import SSHConnection


class EXTSSH(SSHConnection):
    '''
    EXT support
    '''
    def session_preparation(self):
        '''
        EXT requires to be enable mode to disable paging
        '''
        self.enable()
        self.disable_paging(command="disable clipaging\n")
        self.set_base_prompt()
