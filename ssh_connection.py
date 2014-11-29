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

        router_name = self.normalize_linefeeds(router_name)
        self.router_name = router_name.strip()
        self.router_prompt = self.router_name + z_prompt
        if DEBUG: print "router_name: {}; prompt: {}".format(self.router_name, self.router_prompt)

    
    def send_command(self, command_string, delay_factor=1, max_loops=30):
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

        output = self.normalize_linefeeds(output)
        output = self.strip_command(command_string, output)
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

        return output


    def config_mode(self):
        pass

