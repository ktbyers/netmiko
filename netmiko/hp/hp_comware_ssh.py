from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import time

class HPComwareSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''
        
        self.disable_paging(command="\nscreen-length disable\n")
        self.find_prompt()
        
        return None
    
    def config_mode(self):
        '''
        Enter config mode
        '''
        
        DEBUG = False
        
        if self.check_config_mode():
            return True
        
        output = self.send_command('system-view\n')

        if DEBUG: print output
        
        if self.check_config_mode():
            return True
        else:
            return False
        
    def exit_config_mode(self):
        '''
        Exit config mode
        '''
        
        DEBUG = False
        
        if not self.check_config_mode():
            return True
        
        output = self.send_command('return\n')
        
        if DEBUG: print output
        
        if self.check_config_mode():
            return False
        else:
            return True
    
    def check_config_mode(self):
        '''
        Finds the HP Comware prompt and checks if the prompt contains the right config mode characters ']'
        
        '''
        
        self.find_prompt()
        if self.router_prompt[0] == '[' and self.router_prompt[-1] == ']':
            return True
        else:
            return False
    
    def find_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']', delay_factor=1):
        '''
        Finds the HP Comware prompt
        
        '''
        
        self.router_prompt = SSHConnection.find_prompt(self, pri_prompt_terminator, alt_prompt_terminator, delay_factor)
        return self.router_prompt
      