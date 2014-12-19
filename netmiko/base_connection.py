import paramiko
import time
import socket
import re

from netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException


class BaseSSHConnection(object):
    '''
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    '''

    def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False

        if not verbose:
            self.establish_connection(verbose=False)
        else:
            self.establish_connection()

        self.session_preparation()


    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        This method handles some of vagaries that occur between various devices
        early on in the session.

        In general, it should include:
        self.disable_paging()   # if applicable
        self.find_prompt()

        '''

        self.disable_paging()
        self.find_prompt()


    def establish_connection(self, sleep_time=3, verbose=True, timeout=8):
        '''
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(
             paramiko.AutoAddPolicy())

        # initiate SSH connection
        if verbose: print "SSH connection established to {0}:{1}".format(self.ip, self.port)

        try:
            self.remote_conn_pre.connect(hostname=self.ip, port=self.port, 
                        username=self.username, password=self.password,
                        look_for_keys=False, timeout=timeout)
        except socket.error as e:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as e:
            msg = "Authentication failure: unable to connect to device {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            msg += '\n' + str(e)
            raise NetMikoAuthenticationException(msg)

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()
        if verbose: print "Interactive SSH session established"

        # Strip the initial router prompt
        time.sleep(sleep_time)
        return self.remote_conn.recv(MAX_BUFFER)


    def disable_paging(self, command="terminal length 0\n", delay_factor=1):
        '''
        Disable paging default to a Cisco CLI method
        '''

        self.remote_conn.send(command)
        time.sleep(1*delay_factor)

        # Clear the buffer on the screen
        output = self.remote_conn.recv(MAX_BUFFER)
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)

        return output


    def find_prompt(self):
        pass    


    def clear_buffer(self):
        '''
        Read any data available in the channel 
        '''

        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER)
        else:
            return None


    def send_command(self, command_string, delay_factor=.5, max_loops=30, 
              strip_prompt=True, strip_command=True):
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

        # Some platforms have ansi_escape codes
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)

        if DEBUG: print output
        return output


    def strip_prompt(self, a_string):
        '''
        Strip the trailing router prompt from the output
        '''

        response_list = a_string.split('\n')
        if response_list[-1].strip() == self.router_prompt:
            return '\n'.join(response_list[:-1])
        else:
            return a_string


    def strip_command(self, command_string, output):
        '''
        Strip command_string from output string
        '''

        command_length = len(command_string)
        return output[command_length:]


    def normalize_linefeeds(self, a_string):
        '''
        Convert '\r\r\n','\r\n', '\n\r' to '\n
        '''

        newline = re.compile(r'(\r\r\n|\r\n|\n\r)')

        return newline.sub('\n', a_string)


    def enable(self):
        pass


    def config_mode(self):
        pass


    def exit_config_mode(self):
        pass


    def send_config_set(self, config_commands=None):
        pass


    def strip_ansi_escape_codes(self, string_buffer):
        '''
        Remove any ANSI (VT100) ESC codes from the output

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        I have encountered
        
        Current codes that are filtered:
        ^[[24;27H   Position cursor
        ^[[?25h     Show the cursor
        ^[E         Next line
        ^[[2K       Erase line
        ^[[1;24r    Enable scrolling from start to row end
        0x1b = is the escape character [^ in hex

        HP ProCurve's and F5 LTM's require this (possible others)
        '''

        DEBUG = False
        if DEBUG: print "In strip_ansi_escape_codes"
        if DEBUG: print "repr = %s" % repr(string_buffer)

        CODE_POSITION_CURSOR = '\x1b\[\d+;\d+H'
        CODE_SHOW_CURSOR = '\x1b\[\?25h'
        CODE_NEXT_LINE = '\x1bE'
        CODE_ERASE_LINE = '\x1b\[2K'
        CODE_ENABLE_SCROLL = '\x1b\[\d+;\d+r'

        CODE_SET = [ CODE_POSITION_CURSOR, CODE_SHOW_CURSOR, CODE_ERASE_LINE, CODE_ENABLE_SCROLL ]

        output = string_buffer
        for ansi_esc_code in CODE_SET:
            output = re.sub(ansi_esc_code, '', output)

        # CODE_NEXT_LINE must substitute with '\n'
        output = re.sub(CODE_NEXT_LINE, '\n', output)

        if DEBUG:
            print "new_output = %s" % output
            print "repr = %s" % repr(output)

        return output

    
    def cleanup(self):
        '''
        Any needed cleanup before closing connection
        '''
        pass


    def disconnect(self):
        '''
        Gracefully close the SSH connection
        '''

        self.cleanup()
        self.remote_conn_pre.close()


    def commit(self):
        '''
        Commit method for platforms that support this
        '''

        pass
