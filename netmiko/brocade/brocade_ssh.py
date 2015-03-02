from netmiko.ssh_connection import SSHConnection

class BrocadeVdxSSH(SSHConnection):

    def enable(self):
        '''
        No enable mode on Brocade VDX
        '''

    	pass


