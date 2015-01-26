from netmiko.ssh_connection import SSHConnection
import re

class CiscoNxosSSH(SSHConnection):

    def normalize_linefeeds(self, a_string):
	    '''
	    Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text
	    '''

	    newline = re.compile(r'(\r\r\n|\r\n)')

	    return newline.sub('\n', a_string).replace('\r', '')

    def config_mode(self):
        '''
        Exit config mode
        '''
        output = self.send_command('config terminal\n')

        if self.check_config_mode():
            self.clear_buffer()
            return False
        else:
            self.clear_buffer()
            return True

    def exit_config_mode(self):
        '''
        Exit config mode
        '''
        output = self.send_command('end\n')

        if self.check_config_mode():
            self.clear_buffer()
            return False
        else:
            self.clear_buffer()
            return True
	   		
    def check_config_mode(self):
        '''
        Finds the Cisco NXOS prompt and checks if the prompt contains the right config mode characters '(config)#'
        
        '''
        
        self.find_prompt()
        if self.router_prompt[-9:] == '(config)#':
            return True
        else:
            return False