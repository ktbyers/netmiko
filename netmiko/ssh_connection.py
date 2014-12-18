import paramiko
import time

from base_connection import BaseSSHConnection
from netmiko_globals import MAX_BUFFER


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco CLI behavior.
    '''

    def disable_paging(self):
        '''
        Disable paging on a Cisco router
        '''

        self.remote_conn.send("terminal length 0\n")
        time.sleep(1)

        # Clear the buffer on the screen
        return self.remote_conn.recv(MAX_BUFFER)


    def find_prompt(self):
        '''
        Finds the network device name and prompt ('>', '#')
        '''

        DEBUG = False
        if DEBUG: print "In find_prompt"

        self.remote_conn.send("\n")
        time.sleep(1)

        router_name = self.remote_conn.recv(MAX_BUFFER)

        if (router_name.count('>') == 1):
            z_prompt = '>'
            router_name = router_name.split('>')[0]
        elif (router_name.count('#') == 1):
            z_prompt = '#'
            router_name = router_name.split('#')[0]
        else:
            raise ValueError("Router name not found after multiple attempts")

        # Some platforms have ANSI escape codes
        if self.ansi_escape_codes:
            router_name = self.strip_ansi_escape_codes(router_name)
        router_name = self.normalize_linefeeds(router_name)
        self.router_name = router_name.strip()
        self.router_prompt = self.router_name + z_prompt
        if DEBUG: print "router_name: {}; prompt: {}".format(self.router_name, self.router_prompt)


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

