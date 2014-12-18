from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER
import time

class CiscoAsaSSH(SSHConnection):

    def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False

        if not verbose:
            self.establish_connection(verbose=False)
        else:
            self.establish_connection()

        # ASA must go into enable mode to disable_paging
        self.enable()
        self.disable_paging()
        self.find_prompt()


    def disable_paging(self, delay_factor=1):
        '''
        Cisco ASA paging disable 
        Ensures that multi-page output doesn't prompt for user interaction 
        (i.e. --MORE--)

        Must manually control the channel at this point.
        '''

        self.remote_conn.send("terminal pager 0\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)

        return output


    def enable(self, delay_factor=1):
        '''
        Enter enable mode

        Must manually control the channel at this point for ASA
        '''

        self.clear_buffer()
        self.remote_conn.send("\nenable\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        if 'assword' in output:
            self.remote_conn.send(self.secret+'\n')
            self.remote_conn.send('\n')
            time.sleep(1*delay_factor)
            output += self.remote_conn.recv(MAX_BUFFER)

        return None

