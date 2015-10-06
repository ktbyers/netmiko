from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER


class HPComwareSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established
        '''

        self.disable_paging(command="\nscreen-length disable\n")
        self.set_base_prompt()


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


    def set_base_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator=']',
                        delay_factor=.5):
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

        self.clear_buffer()
        self.remote_conn.sendall("\n")
        time.sleep(1*delay_factor)

        prompt = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
        prompt = self.normalize_linefeeds(prompt)

        # If multiple lines in the output take the last line
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()

        # Check that ends with a valid terminator character
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("Router prompt not found: {0}".format(prompt))

        # Strip off leading and trailing terminator
        prompt = prompt[1:-1]
        prompt = prompt.strip()

        self.base_prompt = prompt

        if debug:
            print("prompt: {}".format(self.base_prompt))

        return self.base_prompt
