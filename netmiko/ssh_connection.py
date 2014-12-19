import paramiko
import time

from base_connection import BaseSSHConnection
from netmiko_globals import MAX_BUFFER


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco CLI behavior.
    '''

    def enable(self):
        '''
        Enter enable mode
        '''
        output = self.send_command('enable\n')
        if 'assword' in output:
            output += self.send_command(self.secret)

        self.find_prompt()
        self.clear_buffer()

        return None


    def config_mode(self):
        '''
        First check whether currently already in configuration mode.

        Enter config mode (if necessary)
        '''

        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if not '(config)' in output:
            output += self.send_command('config term\n')
            if not '(config)' in output:
                raise ValueError("Failed to enter configuration mode")

        return output


    def exit_config_mode(self):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''

        # only new_output is returned if 'end' is executed
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if '(config)' in output:
            new_output = self.send_command('end', strip_prompt=False, strip_command=False)
            if '(config)' in new_output:
                raise ValueError("Failed to exit configuration mode")
            return new_output

        return output

