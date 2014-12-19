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
       

    def enable(self, delay_factor=1):
        '''
        tmsh command is equivalent to config command on F5.
        '''
        self.clear_buffer()
        self.remote_conn.send("\ntmsh\n")
        time.sleep(1*delay_factor)

        return None


    def send_command(self, command_string, delay_factor=1):
        '''
        Execute the command_string on SSH channel
        ''' 

        DEBUG = False
        output = ''
        #Ensure there is a new line at the end of the command
        command_string  = command_string.rstrip("\n")
        command_string += '\n'

        if DEBUG: print "Command is: {}".format(command_string)
        self.remote_conn.send(command_string)

        time.sleep(1)

        output = self.remote_conn.recv(MAX_BUFFER)
        output = self.remote_conn.recv(MAX_BUFFER)

        output = self.normalize_linefeeds(output)
        output = self.strip_command(command_string,output)
        
        return output   


    def send_config_set(self, config_commands=None, commit=False):
        '''
        Send in a set of configuration commands as a list

        The command will be executed one after the other

        '''
        DEBUG = False

        output = ''

        if config_commands is None:
            return ''


        if type(config_commands) != type([]):
            raise ValueError("Invalid argument passed into send_config_set")

        for a_command in config_commands:
            output += self.send_command(a_command)
        
        if DEBUG: print output  

        return output
               

    def normalize_linefeeds(self, a_string):
        '''
        Convert '\r\n' or '\r\r\n' to '\n, and remove '\r's in the text
        '''    
        newline = re.compile(r'(\r\n|\r\n\r\n|\r\r\n|\n\r|\r)')

        return newline.sub('\n', a_string)
