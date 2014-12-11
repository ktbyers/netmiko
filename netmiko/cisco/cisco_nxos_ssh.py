from netmiko.ssh_connection import SSHConnection
import re

class CiscoNxosSSH(SSHConnection):

    def strip_prompt(self, a_string):
	    '''
	    Strip the trailing router prompt from the output
	    '''

	    response_list = a_string.split('\n')

	    if response_list[-1].lstrip() == (self.router_prompt + ' '):
	        return '\n'.join(response_list[:-1])
	    else:

	    	return a_string


    def normalize_linefeeds(self, a_string):
	    '''
	    Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text
	    '''

	    newline = re.compile(r'(\r\r\n|\r\n)')

	    return newline.sub('\n', a_string).replace('\r', '')

	   		