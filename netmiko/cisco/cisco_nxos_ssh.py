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
        Enter config mode
        '''
        
        DEBUG = False
        
        if self.check_config_mode():
            return True
        
        output = self.send_command('configure terminal\n')

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
        
        output = self.send_command('end\n')

        if DEBUG: print output

        if self.check_config_mode():
            return False
        else:
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