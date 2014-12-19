from netmiko.base_connection import BaseSSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import time
import re

class F5LtmSSH(BaseSSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''

        self.disable_paging(command="\nset length 0\n")
        time.sleep(1)

        self.tmsh_mode()        
        self.find_prompt()
       

    def tmsh_mode(self, delay_factor=1):
        '''
        tmsh command is equivalent to config command on F5.
        '''
        self.clear_buffer()
        self.remote_conn.send("\ntmsh\n")
        time.sleep(1*delay_factor)
        self.clear_buffer()

        return None


    def normalize_linefeeds(self, a_string):
        '''
        Convert '\r\n' or '\r\r\n' to '\n, and remove '\r's in the text
        '''    
        newline = re.compile(r'(\r\n|\r\n\r\n|\r\r\n|\n\r|\r)')

        return newline.sub('\n', a_string)
