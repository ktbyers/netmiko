from netmiko.ssh_connection import SSHConnection
import re

class CiscoXrSSH(SSHConnection):

    def commit(self):
        '''
        Commit the entered configuration. 

        Raise an error and return the failure if the commit fails.

        Automatically enter and exit configuration mode.
        '''

        # Enter config mode (if necessary)
        output = self.config_mode()

        output += self.send_command('commit', 
                    strip_prompt=False, strip_command=False)

        if "Failed to commit" in output:
            fail_msg = self.send_command('show configuration failed',
                                     strip_prompt=False, strip_command=False)

            raise ValueError('Commit failed with the following errors:\n\n \
                        {fail_msg}'.format(fail_msg=fail_msg))

        output += self.exit_config_mode()
        return output


    def exit_config_mode(self, exit_config='end'):
        '''
        First check whether in configuration mode.

        If so, exit config mode
        '''
        DEBUG = False
        output = ''
        
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if "Uncommitted changes found" in output:
                output += self.send_command('no\n', strip_prompt=False, strip_command=False)
            if DEBUG:
                print output
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
            
        return output


    def normalize_linefeeds(self, a_string):
        '''
        Convert '\r\n','\r\r\n', '\n\r', or '\r' to '\n
        '''

        newline = re.compile(r'(\r\r\n|\r\n|\n\r|\r)')

        return newline.sub('\n', a_string)


