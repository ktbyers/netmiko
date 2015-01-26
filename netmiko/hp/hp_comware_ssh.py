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
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''
        
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if not ']' in output:
            output += self.send_command('system-view\n', strip_prompt=False, strip_command=False)
            if not ']' in output:
                raise ValueError("Failed to enter system view for configuration")

        return output
    
    def exit_config_mode(self):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''

        # only new_output is returned if 'quit' is executed
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if '(config' in output:
            new_output = self.send_command('quit', strip_prompt=False, strip_command=False)
            if ']' in new_output:
                raise ValueError("Failed to exit configuration mode")
            return new_output

        return output
    
    def check_config_mode(self):
        '''
        Finds the HP Comware prompt and checks if the prompt contains the right config mode characters ']'
        
        '''
        
        self.find_prompt()
        if self.router_prompt[-1] == ']':
            return True
        else:
            return False
    
    def find_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']', delay_factor=1):
        '''
        Finds the HP Comware prompt
        
        '''
        
        self.router_prompt = SSHConnection.find_prompt(self, pri_prompt_terminator, alt_prompt_terminator, delay_factor)
        return self.router_prompt    