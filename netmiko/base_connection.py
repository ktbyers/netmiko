'''
Base connection class for netmiko

Handles SSH connection and methods that are generically applicable to different
platforms (Cisco and non-Cisco).

Also defines methods that should generally be supported by child classes
'''

from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import time
import socket
import re
import io

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException


class BaseSSHConnection(object):
    '''
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    '''

    def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True,
                 use_keys=False):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False

        # set in set_base_prompt method
        self.base_prompt = ''

        self.establish_connection(verbose=verbose, use_keys=use_keys)
        self.session_preparation()


    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        This method handles some of vagaries that occur between various devices
        early on in the session.

        In general, it should include:
        self.disable_paging()   # if applicable
        self.set_base_prompt()
        '''

        self.disable_paging()
        self.set_base_prompt()


    def establish_connection(self, sleep_time=3, verbose=True, timeout=8, use_keys=False):
        '''
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException

        use_keys is a boolean that allows ssh-keys to be used for authentication
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # initiate SSH connection
        try:
            self.remote_conn_pre.connect(hostname=self.ip, port=self.port,
                                         username=self.username, password=self.password,
                                         look_for_keys=use_keys, allow_agent=False,
                                         timeout=timeout)
        except socket.error:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as auth_err:
            msg = "Authentication failure: unable to connect {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            msg += '\n' + str(auth_err)
            raise NetMikoAuthenticationException(msg)

        if verbose:
            print("SSH connection established to {0}:{1}".format(self.ip, self.port))

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()
        self.special_login_handler()
        if verbose:
            print("Interactive SSH session established")

        time.sleep(sleep_time)
        # Strip any initial data
        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
        else:
            i = 0
            while i <= 10:
                # Send a newline if no data is present
                self.remote_conn.sendall('\n')
                time.sleep(.5)
                if self.remote_conn.recv_ready():
                    return self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
                else:
                    i += 1
            return ""


    def special_login_handler(self, delay_factor=1):
        '''
        Special handler for devices like WLC, Avaya ERS that throw up characters prior to login
        '''
        pass


    def disable_paging(self, command="terminal length 0\n", delay_factor=.5):
        '''
        Disable paging default to a Cisco CLI method
        '''

        self.remote_conn.sendall(command)
        time.sleep(1*delay_factor)

        # Clear the buffer on the screen
        output = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)

        return output


    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=.5):
        '''
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without '>' or '#').

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode
        '''

        debug = False

        if debug:
            print("In set_base_prompt")

        self.clear_buffer()
        self.remote_conn.sendall("\n")
        time.sleep(1*delay_factor)

        prompt = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')

        # Some platforms have ANSI escape codes
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        prompt = self.normalize_linefeeds(prompt)

        try:
            # If multiple lines in the output take the last line
            prompt = prompt.split('\n')[-1]
            prompt = prompt.strip()

            # Check that ends with a valid terminator character
            if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
                raise ValueError()
        except (IndexError, ValueError):
            if debug:
                print("Router prompt not found: {0}".format(prompt))
            raise ValueError("Router prompt not found: {0}".format(prompt))

        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]

        if debug:
            print("prompt: {0}".format(self.base_prompt))

        return self.base_prompt


    def find_prompt(self, delay_factor=.5):
        '''
        Finds the current network device prompt, last line only
        '''

        debug = False

        if debug:
            print("In find_prompt")

        self.clear_buffer()
        self.remote_conn.sendall("\n")
        time.sleep(1*delay_factor)

        prompt = self.remote_conn.recv(MAX_BUFFER).decode('utf-8')

        # Some platforms have ANSI escape codes
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        prompt = self.normalize_linefeeds(prompt)

        # If multiple lines in the output take the last line
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()

        if debug:
            print("prompt: {}".format(prompt))

        return prompt


    def clear_buffer(self):
        '''
        Read any data available in the channel up to MAX_BUFFER
        '''

        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
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

        debug = False
        output = ''

        if debug:
            print('In send_command')

        self.clear_buffer()

        # Ensure there is a newline at the end of the command
        command_string = command_string.rstrip("\n")
        command_string += '\n'

        if debug:
            print("Command is: {0}".format(command_string))

        self.remote_conn.sendall(command_string)

        time.sleep(1*delay_factor)
        not_done = True
        i = 1

        while (not_done) and (i <= max_loops):
            time.sleep(1*delay_factor)
            i += 1
            # Keep reading data as long as available (up to max_loops)
            if self.remote_conn.recv_ready():
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
            else:
                not_done = False

        # Some platforms have ansi_escape codes
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)

        if debug:
            print(output)
        return output


    def strip_prompt(self, a_string):
        '''
        Strip the trailing router prompt from the output
        '''

        response_list = a_string.split('\n')
        last_line = response_list[-1]

        if self.base_prompt in last_line:
            return '\n'.join(response_list[:-1])
        else:
            return a_string


    def send_command_expect(self, command_string, expect_string=None,
                            delay_factor=.5, max_loops=240,
                            strip_prompt=True, strip_command=True):
        '''
        Send command to network device retrieve output until router_prompt or expect_string

        By default this method will keep waiting to receive data until the network device prompt is
        detected. The network device prompt will be determined by the find_prompt() method.

        command_string = command to execute
        expect_string = pattern to search for in output
        delay_factor = decrease the initial delay before we start looking for data
        max_loops = number of iterations before we give up and raise an exception
        strip_prompt = strip the trailing prompt from the output
        strip_command = strip the leading command from the output
        '''

        debug = False
        output = ''

        # Ensure there is a newline at the end of the command
        command_string = command_string.rstrip("\n")
        command_string += '\n'

        if expect_string is None:
            search_pattern = self.find_prompt()
            time.sleep(delay_factor*1)
        else:
            search_pattern = expect_string

        self.clear_buffer()

        if debug:
            print("Command is: {0}".format(command_string))
            print("Search to stop receiving data is: '{0}'".format(search_pattern))

        self.remote_conn.sendall(command_string)

        # Initial delay after sending command
        time.sleep(delay_factor*1)

        i = 1
        # Keep reading data until search_pattern is found (or max_loops)
        while i <= max_loops:

            if debug:
                print("In while loop")

            if self.remote_conn.recv_ready():
                if debug:
                    print("recv_ready = True")
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8')
                if search_pattern in output:
                    break
            else:
                if debug:
                    print("recv_ready = False")
                # No data, wait a little bit
                time.sleep(delay_factor*1)

            i += 1

        else:   # nobreak
            # search_pattern never found
            raise IOError("Search pattern never detected in send_command_expect: {0}".format(
                search_pattern))


        # Some platforms have ansi_escape codes
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)

        if debug:
            print(output)

        return output


    @staticmethod
    def strip_command(command_string, output):
        '''
        Strip command_string from output string
        '''

        command_length = len(command_string)
        return output[command_length:]


    @staticmethod
    def normalize_linefeeds(a_string):
        '''
        Convert '\r\r\n','\r\n', '\n\r' to '\n
        '''

        newline = re.compile(r'(\r\r\n|\r\n|\n\r)')

        return newline.sub('\n', a_string)


    def enable(self):
        """Disable 'enable()' method."""
        raise AttributeError("Network device does not support 'enable()' method")


    def exit_enable_mode(self, exit_command=''):
        """Disable 'exit_enable_mode()' method."""
        raise AttributeError("Network device does not support 'exit_enable_mode()' method")


    def config_mode(self, config_command=''):
        '''
        Enter into config_mode.

        First check whether currently already in configuration mode.
        Enter config mode (if necessary)
        '''
        output = ''
        if not self.check_config_mode():
            output = self.send_command(config_command, strip_prompt=False, strip_command=False)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode")

        return output


    def exit_config_mode(self, exit_config=''):
        '''
        Exit from configuration mode.
        '''
        output = ''
        if self.check_config_mode():
            output = self.send_command(exit_config, strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")

        return output


    def check_enable_mode(self, check_string=''):
        """Disable 'check_enable_mode()' method."""
        raise AttributeError("Network device does not support 'check_enable_mode()' method")


    def check_config_mode(self, check_string=''):
        '''
        Checks if the device is in configuration mode or not

        Returns a boolean
        '''
        output = self.send_command('\n', strip_prompt=False, strip_command=False)
        if check_string in output:
            return True
        else:
            return False


    def send_config_from_file(self, config_file=None, **kwargs):
        '''
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.
        '''

        try:
            with io.open(config_file, encoding='utf-8') as cfg_file:
                return self.send_config_set(cfg_file, **kwargs)
        except IOError:
            print("I/O Error opening config file: {0}".format(config_file))

        return ''


    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        '''
        Send group of configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.

        **kwargs will allow passing of all the arguments to send_command
        strip_prompt and strip_command will be set to False if not explicitly set in
        the method call.
        '''

        debug = False

        if config_commands is None:
            return ''

        # Set strip_prompt and strip_command to default to False
        kwargs.setdefault('strip_prompt', False)
        kwargs.setdefault('strip_command', False)

        # Config commands must be iterable, but not a string
        if not hasattr(config_commands, '__iter__'):
            raise ValueError("Invalid argument passed into send_config_set")

        # Enter config mode (if necessary)
        output = self.config_mode()

        for a_command in config_commands:
            output += self.send_command(a_command, **kwargs)

        if exit_config_mode:
            output += self.exit_config_mode()

        if debug:
            print(output)

        return output


    @staticmethod
    def strip_ansi_escape_codes(string_buffer):
        '''
        Remove any ANSI (VT100) ESC codes from the output

        http://en.wikipedia.org/wiki/ANSI_escape_code

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        I have encountered

        Current codes that are filtered:
        ESC = '\x1b' or chr(27)
        ESC = is the escape character [^ in hex ('\x1b')
        ESC[24;27H   Position cursor
        ESC[?25h     Show the cursor
        ESC[E        Next line (HP does ESC-E)
        ESC[2K       Erase line
        ESC[1;24r    Enable scrolling from start to row end

        HP ProCurve's and F5 LTM's require this (possible others)
        '''

        debug = False
        if debug:
            print("In strip_ansi_escape_codes")
        if debug:
            print("repr = %s" % repr(string_buffer))

        code_position_cursor = chr(27) + r'\[\d+;\d+H'
        code_show_cursor = chr(27) + r'\[\?25h'
        code_next_line = chr(27) + r'E'
        code_erase_line = chr(27) + r'\[2K'
        code_enable_scroll = chr(27) + r'\[\d+;\d+r'

        code_set = [code_position_cursor, code_show_cursor, code_erase_line, code_enable_scroll]

        output = string_buffer
        for ansi_esc_code in code_set:
            output = re.sub(ansi_esc_code, '', output)

        # CODE_NEXT_LINE must substitute with '\n'
        output = re.sub(code_next_line, '\n', output)

        if debug:
            print("new_output = %s" % output)
            print("repr = %s" % repr(output))

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
        raise AttributeError("Network device does not support 'commit()' method")
