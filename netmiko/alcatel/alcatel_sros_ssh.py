'''
Alcatel-Lucent SROS support
'''
from netmiko.ssh_connection import SSHConnection


class AlcatelSrosSSH(SSHConnection):
    '''
    SROS support
    '''
    def session_preparation(self):
        self.disable_paging(command="\environment no more\n")

    def enable(self):
	pass
