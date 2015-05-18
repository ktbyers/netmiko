from netmiko.ssh_connection import SSHConnection

class BrocadeVdxSSH(SSHConnection):

    def enable(self):
        '''
        No enable mode on Brocade VDX
        '''
        pass


    def exit_enable_mode(self, exit_command=''):
        '''
        No enable mode on Brocade VDX
        '''
        pass

