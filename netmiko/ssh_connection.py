import paramiko
import time

from base_connection import BaseSSHConnection
from netmiko_globals import MAX_BUFFER


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco CLI behavior.
    '''

    def enable_mode(self):
        '''
        Enter enable mode
        '''

        output = self.send_command('enable')
        if 'assword' in output:
            output += self.send_command(self.secret)

        self.find_prompt()
        self.clear_buffer()


    def check_enable_mode(self, check_string='#'):
        '''
        Checks if the device is in enable mode or not

        Returns a boolean
        '''
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if check_string in output:
            return True
        else:
            return False


    def config_mode(self, config_command='config term'):
        '''
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''

        output = ''
        if not self.check_config_mode():
            output = self.send_command(config_command, strip_prompt=False, strip_command=False)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode")

        return output


    def exit_config_mode(self, exit_config='end'):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''

        output = ''
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")

        return output


    def check_config_mode(self, check_string=')#'):
        '''
        Checks if the device is in configuration mode or not

        Returns a boolean
        '''

        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if check_string in output:
            return True
        else:
            return False
