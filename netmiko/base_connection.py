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
from os import path

from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException


class BaseSSHConnection(object):
    """
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    """
    def __init__(self, ip=u'', host=u'', username=u'', password=u'', secret=u'', port=22,
                 device_type=u'', verbose=False, global_delay_factor=.1, use_keys=False,
                 key_file=None, ssh_strict=False, system_host_keys=False, alt_host_keys=False,
                 alt_key_file='', ssh_config_file=None):

        if ip:
            self.host = ip
            self.ip = ip
        elif host:
            self.host = host
        if not ip and not host:
            raise ValueError("Either ip or host must be set")
        self.port = int(port)
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False

        # Use the greater of global_delay_factor or delay_factor local to method
        self.global_delay_factor = global_delay_factor

        # set in set_base_prompt method
        self.base_prompt = ''

        if not ssh_strict:
            self.key_policy = paramiko.AutoAddPolicy()
        else:
            self.key_policy = paramiko.RejectPolicy()

        # Options for SSH host_keys
        self.system_host_keys = system_host_keys
        self.alt_host_keys = alt_host_keys
        self.alt_key_file = alt_key_file

        # For SSH proxy support
        self.ssh_config_file = ssh_config_file

        self.establish_connection(verbose=verbose, use_keys=use_keys, key_file=key_file)
        self.session_preparation()

    def session_preparation(self):
        """
        Prepare the session after the connection has been established

        This method handles some of vagaries that occur between various devices
        early on in the session.

        In general, it should include:
        self.set_base_prompt()
        self.disable_paging()   # if applicable
        """
        self.set_base_prompt()
        self.disable_paging()

    def _use_ssh_config(self, connect_dict):
        """
        Update SSH connection parameters based on contents of SSH 'config' file

        This method modifies the connect_dict dictionary, returns None
        """
        # Use SSHConfig to generate source content.
        full_path = path.abspath(path.expanduser(self.ssh_config_file))
        if path.exists(full_path):
            ssh_config_instance = paramiko.SSHConfig()
            with open(full_path) as f:
                ssh_config_instance.parse(f)
                host_specifier = "{0}:{1}".format(self.host, self.port)
                source = ssh_config_instance.lookup(host_specifier)
        else:
            source = {}

        if source.get('proxycommand'):
            proxy = paramiko.ProxyCommand(source['proxycommand'])
        elif source.get('ProxyCommand'):
            proxy = paramiko.ProxyCommand(source['proxycommand'])
        else:
            proxy = None

        # Only update 'hostname', 'sock', 'port', and 'username'
        # For 'port' and 'username' only update if using object defaults
        if connect_dict['port'] == 22:
            connect_dict['port'] = int(source.get('port', self.port))
        if connect_dict['username'] == '':
            connect_dict['username'] = source.get('username', self.username)
        if proxy:
            connect_dict['sock'] = proxy
        connect_dict['hostname'] = source.get('hostname', self.host)

    def _connect_params_dict(self, use_keys=False, key_file=None, timeout=8):
        """Convert Paramiko connect params to a dictionary."""
        return {
            'hostname': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'look_for_keys': use_keys,
            'allow_agent': False,
            'key_filename': key_file,
            'timeout': timeout,
        }

    def establish_connection(self, sleep_time=3, verbose=True, timeout=8,
                             use_keys=False, key_file=None):
        """
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException

        use_keys is a boolean that allows ssh-keys to be used for authentication
        """

        # Convert Paramiko connection parameters to a dictionary
        ssh_connect_params = self._connect_params_dict(use_keys=use_keys, key_file=key_file,
                                                       timeout=timeout)

        # Check if using SSH 'config' file mainly for SSH proxy support (updates ssh_connect_params)
        if self.ssh_config_file:
            self._use_ssh_config(ssh_connect_params)

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            self.remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            self.remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        self.remote_conn_pre.set_missing_host_key_policy(self.key_policy)

        # initiate SSH connection
        try:
            self.remote_conn_pre.connect(**ssh_connect_params)
        except socket.error:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.host, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as auth_err:
            msg = "Authentication failure: unable to connect {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.host, port=self.port)
            msg += '\n' + str(auth_err)
            raise NetMikoAuthenticationException(msg)

        if verbose:
            print("SSH connection established to {0}:{1}".format(self.host, self.port))

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()
        self.remote_conn.settimeout(timeout)
        self.special_login_handler()
        if verbose:
            print("Interactive SSH session established")

        time.sleep(.1)
        if self.wait_for_recv_ready_newline():
            return self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
        return ""

    def select_delay_factor(self, delay_factor):
        """Choose the greater of delay_factor or self.global_delay_factor."""
        if delay_factor >= self.global_delay_factor:
            return delay_factor
        else:
            return self.global_delay_factor

    def special_login_handler(self, delay_factor=.1):
        """Handler for devices like WLC, Avaya ERS that throw up characters prior to login."""
        pass

    def disable_paging(self, command="terminal length 0", delay_factor=.1):
        """Disable paging default to a Cisco CLI method."""
        debug = False
        time.sleep(1 * delay_factor)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        if debug:
            print("In disable_paging")
            print("Command: {}".format(command))
        self.remote_conn.sendall(self.normalize_cmd(command))
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        if debug:
            print(output)
            print("Exiting disable_paging")
        return output

    def wait_for_recv_ready_newline(self, delay_factor=.1, max_loops=20):
        """Wait for data to be in the buffer so it can be received."""
        i = 0
        time.sleep(delay_factor)
        while i <= max_loops:
            if self.remote_conn.recv_ready():
                return True
            else:
                self.remote_conn.sendall('\n')
                delay_factor = delay_factor * 1.1
                if delay_factor >= 8:
                    delay_factor = 8
                time.sleep(delay_factor)
                i += 1
        raise NetMikoTimeoutException("Timed out waiting for recv_ready")

    def wait_for_recv_ready(self, delay_factor=.1, max_loops=100, send_newline=False):
        """Wait for data to be in the buffer so it can be received."""
        i = 0
        time.sleep(delay_factor)
        while i <= max_loops:
            if self.remote_conn.recv_ready():
                return True
            else:
                time.sleep(delay_factor)
                i += 1
        raise NetMikoTimeoutException("Timed out waiting for recv_ready")

    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=.1):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without '>' or '#').

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("Router prompt not found: {0}".format(prompt))
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def find_prompt(self, delay_factor=.1):
        """Finds the current network device prompt, last line only."""
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.remote_conn.sendall("\n")
        time.sleep(delay_factor)
        prompt = ''

        if debug:
            print("aaa: {}".format(prompt))
        # Initial attempt to get prompt
        if self.remote_conn.recv_ready():
            prompt = self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
            prompt = prompt.strip()
            if self.ansi_escape_codes:
                prompt = self.strip_ansi_escape_codes(prompt)

        if debug:
            print("bbb: {}".format(prompt))
        # Check if the only thing you received was a newline
        count = 0
        while count <= 10 and not prompt:
            if self.wait_for_recv_ready():
                prompt = self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if debug:
                    print("ccc1: {}".format(repr(prompt)))
                    print("ccc2: {}".format(prompt))
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt)
                prompt = prompt.strip()
            count += 1

        if debug:
            print("ddd: {}".format(prompt))
        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Unable to find prompt: {}".format(prompt))
        time.sleep(delay_factor)
        self.clear_buffer()
        return prompt

    def clear_buffer(self):
        '''Read any data available in the channel up to MAX_BUFFER'''
        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
        else:
            return None

    def send_command(self, command_string, delay_factor=.1, max_loops=150,
                     strip_prompt=True, strip_command=True):
        '''
        Execute command_string on the SSH channel.

        Use delay based mechanism to obtain output.  Strips echoed characters and router prompt.

        delay_factor can be used to increase the delays.

        max_loops can be used to increase the number of times it reads the data buffer

        Returns the output of the command.
        '''
        debug = False
        if debug:
            print('In send_command')

        delay_factor = self.select_delay_factor(delay_factor)
        output = ''
        self.clear_buffer()
        command_string = self.normalize_cmd(command_string)
        if debug:
            print("Command is: {0}".format(command_string))

        self.remote_conn.sendall(command_string)
        for tmp_output in self.receive_data_generator(delay_factor=delay_factor,
                                                      max_loops=max_loops):
            output += tmp_output

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

    def read_until_prompt(self):
        """Read channel until self.base_prompt detected. Return ALL data available."""
        return self.read_until_pattern()

    def read_until_pattern(self, pattern='', re_flags=0):
        """Read channel until pattern detected. Return ALL data available."""
        debug = False
        output = ''
        if not pattern:
            pattern = self.base_prompt
        pattern = re.escape(pattern)
        if debug:
            print("Pattern is: {}".format(pattern))
        while True:
            try:
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if re.search(pattern, output, flags=re_flags):
                    if debug:
                        print("Pattern found: {} {}".format(pattern, output))
                    return output
            except socket.timeout:
                raise NetMikoTimeoutException("Timed-out reading channel, data not available.")

    def read_until_prompt_or_pattern(self, pattern='', re_flags=0):
        """Read until either self.base_prompt or pattern is detected. Return ALL data available."""
        output = ''
        if not pattern:
            pattern = self.base_prompt
        pattern = re.escape(pattern)
        base_prompt_pattern = re.escape(self.base_prompt)
        while True:
            try:
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if re.search(pattern, output, flags=re_flags) or re.search(base_prompt_pattern,
                                                                           output, flags=re_flags):
                    return output
            except socket.timeout:
                raise NetMikoTimeoutException("Timed-out reading channel, data not available.")

    def send_command_expect(self, command_string, expect_string=None,
                            delay_factor=.2, max_loops=500, auto_find_prompt=True,
                            strip_prompt=True, strip_command=True):
        '''
        Send command to network device retrieve output until router_prompt or expect_string

        By default this method will keep waiting to receive data until the network device prompt is
        detected. The current network device prompt will be determined automatically.

        command_string = command to execute
        expect_string = pattern to search for uses re.search (use raw strings)
        delay_factor = decrease the initial delay before we start looking for data
        max_loops = number of iterations before we give up and raise an exception
        strip_prompt = strip the trailing prompt from the output
        strip_command = strip the leading command from the output

        self.global_delay_factor is not used (to make this method faster)
        '''
        debug = False

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
                if debug:
                    print("Found prompt: {}".format(prompt))
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        command_string = self.normalize_cmd(command_string)
        if debug:
            print("Command is: {0}".format(command_string))
            print("Search to stop receiving data is: '{0}'".format(search_pattern))

        time.sleep(delay_factor * 1)
        self.clear_buffer()
        self.remote_conn.sendall(command_string)

        # Initial delay after sending command
        i = 1
        # Keep reading data until search_pattern is found (or max_loops)
        output = ''
        while i <= max_loops:
            if self.remote_conn.recv_ready():
                output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                if debug:
                    print("{}:{}".format(i, output))
                try:
                    lines = output.split("\n")
                    first_line = lines[0]
                    # First line is the echo line containing the command. In certain situations
                    # it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re.sub(pattern, repl='', string=first_line)
                        lines[0] = first_line
                        output = "\n".join(lines)
                except IndexError:
                    pass
                if re.search(search_pattern, output):
                    break
            else:
                time.sleep(delay_factor * 1)
            i += 1
        else:   # nobreak
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
        return output

    @staticmethod
    def strip_backspaces(output):
        """Strip any backspace characters out of the output."""
        backspace_char = '\x08'
        return output.replace(backspace_char, '')

    @staticmethod
    def strip_command(command_string, output):
        """
        Strip command_string from output string

        Cisco IOS adds backspaces into output for long commands (i.e. for commands that line wrap)
        """
        backspace_char = '\x08'

        # Check for line wrap (remove backspaces)
        if backspace_char in output:
            output = output.replace(backspace_char, '')
            output_lines = output.split("\n")
            new_output = output_lines[1:]
            return "\n".join(new_output)
        else:
            command_length = len(command_string)
            return output[command_length:]

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\r\n','\r\n', '\n\r' to '\n."""
        newline = re.compile(r'(\r\r\n|\r\n|\n\r)')
        return newline.sub('\n', a_string)

    @staticmethod
    def normalize_cmd(command):
        """Normalize CLI commands to have a single trailing newline."""
        command = command.rstrip("\n")
        command += '\n'
        return command

    def check_enable_mode(self, check_string=''):
        """Check if in enable mode. Return boolean."""
        self.remote_conn.sendall('\n')
        output = self.read_until_prompt()
        return check_string in output

    def enable(self, cmd='', pattern='password', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        output = ""
        if not self.check_enable_mode():
            self.remote_conn.sendall(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            self.remote_conn.sendall(self.normalize_cmd(self.secret))
            output += self.read_until_prompt()
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output

    def exit_enable_mode(self, exit_command=''):
        """Exit enable mode."""
        output = ""
        if self.check_enable_mode():
            self.remote_conn.sendall(self.normalize_cmd(exit_command))
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(self, check_string='', pattern=''):
        """Checks if the device is in configuration mode or not."""
        self.remote_conn.sendall('\n')
        output = self.read_until_pattern(pattern=pattern)
        return check_string in output

    def config_mode(self, config_command='', pattern=''):
        """Enter into config_mode."""
        output = ''
        if not self.check_config_mode():
            self.remote_conn.sendall(self.normalize_cmd(config_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_config_mode(self, exit_config='', pattern=''):
        """Exit from configuration mode."""
        output = ''
        if self.check_config_mode():
            self.remote_conn.sendall(self.normalize_cmd(exit_config))
            output = self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def receive_data_generator(self, delay_factor=.1, max_loops=150):
        """Generator to collect all data available in channel."""
        i = 0
        while i <= max_loops:
            time.sleep(delay_factor)
            if self.remote_conn.recv_ready():
                yield self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
            else:
                # Safeguard to make sure really done
                time.sleep(delay_factor * 8)
                if not self.remote_conn.recv_ready():
                    break
            i += 1

    def send_config_from_file(self, config_file=None, **kwargs):
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.
        """
        with io.open(config_file, encoding='utf-8') as cfg_file:
            return self.send_config_set(cfg_file, **kwargs)

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=.1,
                        max_loops=150, strip_prompt=False, strip_command=False):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.
        """
        debug = False

        if config_commands is None:
            return ''
        if not hasattr(config_commands, '__iter__'):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = self.config_mode()
        for cmd in config_commands:
            self.remote_conn.sendall(self.normalize_cmd(cmd))
            time.sleep(delay_factor / 2.0)

        # Gather output
        for tmp_output in self.receive_data_generator(delay_factor=delay_factor,
                                                      max_loops=max_loops):
            output += tmp_output
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
