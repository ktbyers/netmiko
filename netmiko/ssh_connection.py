import paramiko
import time

from base_connection import BaseSSHConnection
from netmiko_globals import MAX_BUFFER


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco CLI behavior.
    '''

    def find_prompt(self):
        '''
        Finds the network device prompt

        Assumes the prompt ends in either: '>' or '#'
        '''

        DEBUG = False
        if DEBUG: print "In find_prompt"

        self.clear_buffer()
        self.remote_conn.send("\n")
        time.sleep(1)

        prompt = self.remote_conn.recv(MAX_BUFFER)

        if not (prompt.count('>') == 1 or prompt.count('#') == 1):
            raise ValueError("Router name not found after multiple attempts")

        # Some platforms have ANSI escape codes
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        prompt = self.normalize_linefeeds(prompt)
        self.router_prompt = prompt.strip()
        if DEBUG: print "prompt: {}".format(self.router_prompt)


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


    def send_config_set(self, config_commands=None, commit=False):
        '''
        Send in a set of configuration commands as a list

        The commands will be executed one after the other

        Automatically exits/enters configuration mode.
        '''

        if config_commands is None:
            return ''

        if type(config_commands) != type([]):
            raise ValueError("Invalid argument passed into send_config_set")

        # Enter config mode (if necessary)
        output = self.config_mode()

        for a_command in config_commands:
            output += self.send_command(a_command, strip_prompt=False, strip_command=False)

        if commit:
            output += self.commit()

        output += self.exit_config_mode()

        return output

