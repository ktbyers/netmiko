from __future__ import print_function
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class Huawei_usgv5_SSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging(command="screen-length 0 temporary\n")

    def config_mode(self, config_command='system-view'):
        """Enter configuration mode."""
        return super(Huawei_usgv5_SSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='return'):
        """Exit configuration mode."""
        return super(Huawei_usgv5_SSH, self).exit_config_mode(exit_config=exit_config)

    def check_config_mode(self, check_string=']'):
        """Checks whether in configuration mode. Returns a boolean."""
        return super(Huawei_usgv5_SSH, self).check_config_mode(check_string=check_string)

    def set_base_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']',
                        delay_factor=1):
        '''
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Comware
        this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        '''
        debug = False
        if debug:
            print("In set_base_prompt")

        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel("\n")
        time.sleep(.5 * delay_factor)

        prompt = self.read_channel()
        prompt = self.normalize_linefeeds(prompt)

        # If multiple lines in the output take the last line
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()

        # Check that ends with a valid terminator character
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("Router prompt not found: {0}".format(prompt))
		
		
       # Strip off leading and trailing terminator
       
       #The prompt will be different based on which mode the device is in (normal or high availability)
       	
        if re.match("(^<)", prompt):
            prompt = prompt[1:-1]	   
            prompt = prompt.strip()
            
        else:
            prompt = prompt[6:-1]
            prompt = prompt.strip()
            
            
        self.base_prompt = prompt

        if debug:
            print("prompt: {}".format(self.base_prompt))

        return self.base_prompt
		
	
