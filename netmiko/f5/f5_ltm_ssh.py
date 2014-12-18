from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import time
import re

class F5LtmSSH(SSHConnection):

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

        self.disable_paging()
        time.sleep(1)            
       

    def disable_paging(self, delay_factor=1):
        '''
        Ensures that multi-page output doesn't prompt for user interaction
        (i.e. --MORE--)
        
        On F5 LTM devices, 'set length 0' is equivalent to 'terminal length 0' for disabling paging    

        '''            
        DEBUG = True
        self.remote_conn.send("\n")
        self.remote_conn.send('set length 0\n')
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        if DEBUG: print "Paging has been disabled\n"

        return output
        
    def strip_command(self, command_string, output):
        '''
        Strip command_string from output string
        '''

        command_length = len(command_string)
        return output[command_length:]
        
    

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
