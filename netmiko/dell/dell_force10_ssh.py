'''
Dell Force10 Driver - supports DNOS9
'''
from netmiko.ssh_connection import SSHConnection


class DellForce10SSH(SSHConnection):
    '''
    Dell Force10 Driver - supports DNOS9
    '''
    def cleanup(self):
        '''
        Gracefully exit the SSH session.
        '''
        self.exit_config_mode()
        self.remote_conn.sendall("exit\n")
