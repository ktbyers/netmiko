import paramiko
import time

from base_connection import BaseSSHConnection
from netmiko_globals import MAX_BUFFER


class SSHConnection(BaseSSHConnection):
    '''
    Based upon Cisco IOS behavior.
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

        # .strip_ansi_escape_codes does nothing unless overridden in child-class
        router_name = self.strip_ansi_escape_codes(router_name)
        router_name = self.normalize_linefeeds(router_name)
        self.router_name = router_name.strip()
        self.router_prompt = self.router_name + z_prompt
        if DEBUG: print "router_name: {}; prompt: {}".format(self.router_name, self.router_prompt)


    def send_command(self, command_string, delay_factor=.5, max_loops=30, strip_prompt=True, strip_command=True):
        '''
        Execute command_string on the SSH channel.

        Use delay based mechanism to obtain output.  Strips echoed characters and router prompt.

        delay_factor can be used to increase the delays.

        max_loops can be used to increase the number of times it reads the data buffer

        Returns the output of the command.
        '''

        DEBUG = False
        output = ''

        if DEBUG: print 'In send_command'

        self.clear_buffer()

        # Ensure there is a newline at the end of the command
        command_string = command_string.rstrip("\n")
        command_string += '\n'

        if DEBUG: print "Command is: {}".format(command_string)

        self.remote_conn.send(command_string)

        time.sleep(1*delay_factor)
        not_done = True
        i = 1

        while (not_done) and (i <= max_loops):

            if DEBUG: print "In while loop"
            time.sleep(2*delay_factor)
            i += 1

            # Keep reading data as long as available (up to max_loops)
            if self.remote_conn.recv_ready():
                if DEBUG: print "recv_ready = True"
                output += self.remote_conn.recv(MAX_BUFFER)
            else:
                if DEBUG: print "recv_ready = False"
                not_done = False

        # .strip_ansi_escape_codes does nothing unless overridden in child-class
        output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)

        if DEBUG: print output
        return output


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
        output = self.send_command('end', strip_prompt=False, strip_command=False)
        if '(config)' in output:
            raise ValueError("Failed to exit configuration mode")
        return output


    def send_config_set(self, config_commands=None):
        '''
        Send in a set of configuration commands as a list

        The commands will be executed one after the other

        Automatically exits/enters configuration mode.
        '''

        if config_commands is None:
            return ''

        if type(config_commands) != type([]):
            raise ValueError("Invalid argument passed into send_config_set")

        # Check if already in config mode
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if not '(config)' in output:
            output += self.config_mode()

        for a_command in config_commands:
            output += self.send_command(a_command, strip_prompt=False, strip_command=False)

        output += self.exit_config_mode()

        return output

