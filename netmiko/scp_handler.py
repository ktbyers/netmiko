'''
Create a SCP side-channel to transfer a file to remote network device
'''

from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import scp


class SCPConn(object):
    '''
    Establish an SCP channel to the remote network

    SCP requires a separate SSH connection at least to Cisco IOS
    '''

    def __init__(self, ssh_conn):
        self.ip = ssh_conn.ip
        self.port = ssh_conn.port
        self.username = ssh_conn.username
        self.password = ssh_conn.password
        self.secret = ssh_conn.secret
        self.device_type = ssh_conn.device_type

        self.establish_scp_conn()


    def establish_scp_conn(self):
        '''
        Establish the SCP connection
        '''

        self.scp_conn = paramiko.SSHClient()
        self.scp_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.self.connect(hostname=self.ip, port=self.port, username=self.username,
                          password=self.password, look_for_keys=False, allow_agent=False,
                          timeout=8)

        self.scp_client = scp.SCPClient(ssh.get_transport())


    def scp_transfer_file(self, source_file, dest_file):
        '''
        Transfer file using SCP
        '''

        print("Transferring file: {}".format(source_file))
        self.scp_client.put(source_file, dest_file)


    def close_conn(self):
        '''
        Close the SCP connection
        '''

        self.scp_conn.close()
