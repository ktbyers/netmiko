'''
ENT support
'''
from netmiko.ssh_connection import SSHConnection


class ENTSSH(SSHConnection):
    '''
    ENT support
    '''
    def session_preparation(self):
        '''
        ENT requires to be enable mode to disable paging
        '''
        self.enable()
        self.disable_paging(command="set length 0\n")
        self.set_base_prompt()
