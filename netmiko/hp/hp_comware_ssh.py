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
        
    
    def config_mode(self, config_command='system-view'):
        '''
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''

        # Call parent class with different command for entering config mode
        return super(HPComwareSSH, self).config_mode(config_command=config_command)

        
    def exit_config_mode(self, exit_config='return'):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''

        # Call parent class with different command for exiting config mode
        return super(HPComwareSSH, self).exit_config_mode(exit_config=exit_config)
        
        
    def check_config_mode(self, check_string=']'):
        '''
        Checks if the device is in configuration mode or not

        Returns a boolean
        '''

        # Call parent class with different command for exiting config mode
        return super(HPComwareSSH, self).check_config_mode(check_string=check_string)
       
    
    def find_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']', delay_factor=1):
        '''
        Finds the HP Comware prompt
        '''
        
        # Call parent class with different command for exiting config mode
        return super(HPComwareSSH, self).find_prompt(pri_prompt_terminator=pri_prompt_terminator,
                                                     alt_prompt_terminator=alt_prompt_terminator)

      
