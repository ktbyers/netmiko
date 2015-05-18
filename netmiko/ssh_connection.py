'''
SSHConnection is netmiko SSH class for Cisco and Cisco-like platforms

Exports SSHConnection class
'''
from __future__ import unicode_literals
from netmiko.base_connection import BaseSSHConnection


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco CLI behavior.
    '''

    def enable(self):
        '''
        Enter enable mode
        '''

        output = self.send_command('enable')
        if 'password' in output.lower():
            output += self.send_command(self.secret)

        self.set_base_prompt()
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

        # Call parent class with specific command for entering config mode
        return super(SSHConnection, self).config_mode(config_command=config_command)


    def check_config_mode(self, check_string=')#'):
        '''
        Checks if the device is in configuration mode or not

        Returns a boolean
        '''

        # Call super class with Cisco check string
        return super(SSHConnection, self).check_config_mode(check_string=check_string)


    def exit_config_mode(self, exit_config='end'):
        '''
        Exit from configuration mode.
        '''

        # Call super class with Cisco check string
        return super(SSHConnection, self).exit_config_mode(exit_config=exit_config)


    def exit_enable_mode(self, exit_command='disable'):
        '''
        Exits enable (privileged exec) mode.
        '''
        output = ""
        if self.check_enable_mode():
            output = self.send_command(exit_command, strip_prompt=False, strip_command=False)
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

