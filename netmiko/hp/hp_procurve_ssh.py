from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import re
import time

class HPProcurveSSH(SSHConnection):

    def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type

        if not verbose:
            self.establish_connection(verbose=False)
        else:
            self.establish_connection()

        # HP sends up - 'Press any key to continue'
        time.sleep(1)
        self.remote_conn.send("\n")
        time.sleep(1)

        self.disable_paging()
        self.find_prompt()


    def find_prompt(self, *args, **kwargs, strip_ansi_escape=True):
        '''
        Call parent method with strip_ansi_escape=True
        '''
        super(HPProcurveSSH, self).find_prompt(*args, **kwargs, 
                                    strip_ansi_escape=strip_ansi_escape)


    def send_command(self, *args, **kwargs, strip_ansi_escape=True):
        '''
        Call parent method with strip_ansi_escape=True
        '''
        super(HPProcurveSSH, self).send_command(*args, **kwargs, 
                                        strip_ansi_escape=strip_ansi_escape)


    def disable_paging(self, delay_factor=1):
        '''
        Ensures that multi-page output doesn't prompt for user interaction 
        (i.e. --MORE--)

        Must manually control the channel at this point.
        '''

        self.remote_conn.send("\n")
        self.remote_conn.send("no page\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        return output


    def enable(self):
        '''
        Enter enable mode

        Not implemented on ProCurve just SSH as Manager
        '''

        return None
