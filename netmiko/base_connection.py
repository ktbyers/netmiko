'''
Base connection class for netmiko

Handles SSH connection and methods that are generically applicable to different
platforms (Cisco and non-Cisco).

Also defines methods that should generally be supported by child classes
'''

from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import telnetlib
import time
import socket
import re
import io
from os import path

from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
from netmiko.utilities import write_bytes


class BaseConnection(object):
    """
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    """
    def __init__(self, ip='', host='', username='', password='', secret='', port=None,
                 device_type='', verbose=False, global_delay_factor=1, use_keys=False,
                 key_file=None, allow_agent=False, ssh_strict=False, system_host_keys=False,
                 alt_host_keys=False, alt_key_file='', ssh_config_file=None, timeout=8):

        if ip:
            self.host = ip
            self.ip = ip
        elif host:
            self.host = host
        if not ip and not host:
            raise ValueError("Either ip or host must be set")
        if port is None:
            if 'telnet' in device_type:
                self.port = 23
            else:
                self.port = 22
        else:
            self.port = int(port)
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False
        self.verbose = verbose
        self.timeout = timeout

        # Use the greater of global_delay_factor or delay_factor local to method
        self.global_delay_factor = global_delay_factor

        # set in set_base_prompt method
        self.base_prompt = ''

        # determine if telnet or SSH
        if '_telnet' in device_type:
            self.protocol = 'telnet'
            self.establish_connection()
            self.session_preparation()
        else:
            self.protocol = 'ssh'

            if not ssh_strict:
                self.key_policy = paramiko.AutoAddPolicy()
            else:
                self.key_policy = paramiko.RejectPolicy()

            # Options for SSH host_keys
            self.use_keys = use_keys
            self.key_file = key_file
            self.allow_agent = allow_agent
            self.system_host_keys = system_host_keys
            self.alt_host_keys = alt_host_keys
            self.alt_key_file = alt_key_file

            # For SSH proxy support
            self.ssh_config_file = ssh_config_file

            self.establish_connection()
            self.session_preparation()

        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def write_channel(self, out_data):
        """Generic handler that will write to both SSH and telnet channel."""
        if self.protocol == 'ssh':
            self.remote_conn.sendall(write_bytes(out_data))
        elif self.protocol == 'telnet':
            self.remote_conn.write(write_bytes(out_data))
        else:
            raise ValueError("Invalid protocol specified")

    def read_channel(self):
        """Generic handler that will read all the data from an SSH or telnet channel."""
        if self.protocol == 'ssh':
            output = ""
            while True:
                if self.remote_conn.recv_ready():
                    output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                else:
                    return output
        elif self.protocol == 'telnet':
            return self.remote_conn.read_very_eager().decode('utf-8', 'ignore')

    def _read_channel_expect(self, pattern='', re_flags=0):
        """
        Function that reads channel until pattern is detected.

        pattern takes a regular expression.

        By default pattern will be self.base_prompt

        Note: this currently reads beyond pattern. In the case of SSH it reads MAX_BUFFER.
        In the case of telnet it reads all non-blocking data.

        There are dependecies here like determining whether in config_mode that are actually
        depending on reading beyond pattern.
        """
        debug = False
        output = ''
        if not pattern:
            pattern = self.base_prompt
        pattern = re.escape(pattern)
        if debug:
            print("Pattern is: {}".format(pattern))

        # Will loop for self.timeout time (unless modified by global_delay_factor)
        i = 1
        loop_delay = .1
        max_loops = self.timeout / loop_delay
        while i < max_loops:
            if self.protocol == 'ssh':
                try:
                    # If no data available will wait timeout seconds trying to read
                    output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                except socket.timeout:
                    raise NetMikoTimeoutException("Timed-out reading channel, data not available.")
            elif self.protocol == 'telnet':
                output += self.read_channel()
            if re.search(pattern, output, flags=re_flags):
                if debug:
                    print("Pattern found: {} {}".format(pattern, output))
                return output
            time.sleep(loop_delay * self.global_delay_factor)
            i += 1
        raise NetMikoTimeoutException("Timed-out reading channel, pattern not found in output: {}"
                                      .format(pattern))

    def _read_channel_timing(self, delay_factor=1, max_loops=150):
        """
        Read data on the channel based on timing delays.

        Attempt to read channel max_loops number of times. If no data this will cause a 15 second
        delay.

        Once data is encountered read channel for another two seconds (2 * delay_factor) to make
        sure reading of channel is complete.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        channel_data = ""
        i = 0
        while i <= max_loops:
            time.sleep(.1 * delay_factor)
            new_data = self.read_channel()
            if new_data:
                channel_data += new_data
            else:
                # Safeguard to make sure really done
                time.sleep(2 * delay_factor)
                new_data = self.read_channel()
                if not new_data:
                    break
                else:
                    channel_data += new_data
            i += 1
        return channel_data

    def read_until_prompt(self, *args, **kwargs):
        """Read channel until self.base_prompt detected. Return ALL data available."""
        return self._read_channel_expect(*args, **kwargs)

    def read_until_pattern(self, *args, **kwargs):
        """Read channel until pattern detected. Return ALL data available."""
        return self._read_channel_expect(*args, **kwargs)

    def read_until_prompt_or_pattern(self, pattern='', re_flags=0):
        """Read until either self.base_prompt or pattern is detected. Return ALL data available."""
        output = ''
        if not pattern:
            pattern = self.base_prompt
        pattern = re.escape(pattern)
        base_prompt_pattern = re.escape(self.base_prompt)
        while True:
            try:
                output += self.read_channel()
                if re.search(pattern, output, flags=re_flags) or re.search(base_prompt_pattern,
                                                                           output, flags=re_flags):
                    return output
            except socket.timeout:
                raise NetMikoTimeoutException("Timed-out reading channel, data not available.")

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        debug = False
        if debug:
            print("In telnet_login():")
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ''
        return_msg = ''
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output
                if debug:
                    print(output)
                if re.search(r"sername", output):
                    self.write_channel(self.username + '\n')
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if debug:
                        print("checkpoint1")
                        print(output)
                if re.search(r"assword", output):
                    self.write_channel(self.password + "\n")
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if debug:
                        print("checkpoint2")
                        print(output)
                    if pri_prompt_terminator in output or alt_prompt_terminator in output:
                        if debug:
                            print("checkpoint3")
                        return return_msg
                if re.search(r"assword required, but none set", output):
                    if debug:
                        print("checkpoint4")
                    msg = "Telnet login failed - Password required, but none set: {0}".format(
                        self.host)
                    raise NetMikoAuthenticationException(msg)
                if pri_prompt_terminator in output or alt_prompt_terminator in output:
                    if debug:
                        print("checkpoint5")
                    return return_msg
                self.write_channel("\n")
                time.sleep(.5 * delay_factor)
                i += 1
            except EOFError:
                msg = "Telnet login failed: {0}".format(self.host)
                raise NetMikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel("\n")
        time.sleep(.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if pri_prompt_terminator in output or alt_prompt_terminator in output:
            if debug:
                print("checkpoint6")
            return return_msg

        msg = "Telnet login failed: {0}".format(self.host)
        raise NetMikoAuthenticationException(msg)

    def session_preparation(self):
        """
        Prepare the session after the connection has been established

        This method handles some of vagaries that occur between various devices
        early on in the session.

        In general, it should include:
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()
        """
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()

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

    def _connect_params_dict(self):
        """Convert Paramiko connect params to a dictionary."""
        return {
            'hostname': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'look_for_keys': self.use_keys,
            'allow_agent': self.allow_agent,
            'key_filename': self.key_file,
            'timeout': self.timeout,
        }

    def _sanitize_output(self, output, strip_command=False, command_string=None,
                         strip_prompt=False):
        """Sanitize the output."""
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command and command_string:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)
        return output

    def establish_connection(self, width=None, height=None):
        """
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException

        width and height are needed for Fortinet paging setting.
        """
        if self.protocol == 'telnet':
            self.remote_conn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
            self.telnet_login()
        elif self.protocol == 'ssh':

            # Convert Paramiko connection parameters to a dictionary
            ssh_connect_params = self._connect_params_dict()

            # Check if using SSH 'config' file mainly for SSH proxy support
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

            if self.verbose:
                print("SSH connection established to {0}:{1}".format(self.host, self.port))

            # Use invoke_shell to establish an 'interactive session'
            if width and height:
                self.remote_conn = self.remote_conn_pre.invoke_shell(term='vt100', width=width,
                                                                     height=height)
            else:
                self.remote_conn = self.remote_conn_pre.invoke_shell()

            self.remote_conn.settimeout(self.timeout)
            self.special_login_handler()
            if self.verbose:
                print("Interactive SSH session established")

        # make sure you can read the channel
        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)
        main_delay = delay_factor * .1
        time.sleep(main_delay)
        while i <= 40:
            new_data = self.read_channel()
            if new_data:
                break
            else:
                self.write_channel('\n')
                main_delay = main_delay * 1.1
                if main_delay >= 8:
                    main_delay = 8
                time.sleep(main_delay)
                i += 1
        # check if data was ever present
        if new_data:
            return ""
        else:
            raise NetMikoTimeoutException("Timed out waiting for data")

    def select_delay_factor(self, delay_factor):
        """Choose the greater of delay_factor or self.global_delay_factor."""
        if delay_factor >= self.global_delay_factor:
            return delay_factor
        else:
            return self.global_delay_factor

    def special_login_handler(self, delay_factor=1):
        """Handler for devices like WLC, Avaya ERS that throw up characters prior to login."""
        pass

    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """Disable paging default to a Cisco CLI method."""
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        if debug:
            print("In disable_paging")
            print("Command: {}".format(command))
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        if debug:
            print(output)
            print("Exiting disable_paging")
        return output

    def set_terminal_width(self, command="", delay_factor=1):
        """
        CLI terminals try to automatically adjust the line based on the width of the terminal.
        This causes the output to get distorted when accessed programmatically.

        Set terminal width to 511 which works on a broad set of devices.
        """
        if not command:
            return ""
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        command = self.normalize_cmd(command)
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        if debug:
            print(output)
            print("Exiting set_terminal_width")
        return output

    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=1):
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

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only."""
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel("\n")
        time.sleep(delay_factor * .1)

        # Initial attempt to get prompt
        prompt = self.read_channel().strip()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        if debug:
            print("prompt1: {}".format(prompt))

        # Check if the only thing you received was a newline
        count = 0
        while count <= 10 and not prompt:
            prompt = self.read_channel().strip()
            if prompt:
                if debug:
                    print("prompt2a: {}".format(repr(prompt)))
                    print("prompt2b: {}".format(prompt))
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt).strip()
            else:
                self.write_channel("\n")
                time.sleep(delay_factor * .1)
            count += 1

        if debug:
            print("prompt3: {}".format(prompt))
        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split('\n')[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Unable to find prompt: {}".format(prompt))
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        return prompt

    def clear_buffer(self):
        """Read any data available in the channel."""
        self.read_channel()

    def send_command_timing(self, command_string, delay_factor=1, max_loops=150,
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
            print('In send_command_timing')

        delay_factor = self.select_delay_factor(delay_factor)
        output = ''
        self.clear_buffer()
        command_string = self.normalize_cmd(command_string)
        if debug:
            print("Command is: {0}".format(command_string))

        self.write_channel(command_string)
        output = self._read_channel_timing(delay_factor=delay_factor, max_loops=max_loops)
        if debug:
            print("zzz: {}".format(output))
        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)
        if debug:
            print(output)
        return output

    def strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output."""
        response_list = a_string.split('\n')
        last_line = response_list[-1]
        if self.base_prompt in last_line:
            return '\n'.join(response_list[:-1])
        else:
            return a_string

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
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
        '''
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)

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

        time.sleep(delay_factor * .2)
        self.clear_buffer()
        self.write_channel(command_string)

        # Initial delay after sending command
        i = 1
        # Keep reading data until search_pattern is found (or max_loops)
        output = ''
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                output += new_data
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
                time.sleep(delay_factor * .2)
            i += 1
        else:   # nobreak
            raise IOError("Search pattern never detected in send_command_expect: {0}".format(
                search_pattern))

        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)
        return output

    def send_command_expect(self, *args, **kwargs):
        """Support previous name of send_command method."""
        return self.send_command(*args, **kwargs)

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
        newline = re.compile(r'(\r\r\r\n|\r\r\n|\r\n|\n\r)')
        return newline.sub('\n', a_string)

    @staticmethod
    def normalize_cmd(command):
        """Normalize CLI commands to have a single trailing newline."""
        command = command.rstrip("\n")
        command += '\n'
        return command

    def check_enable_mode(self, check_string=''):
        """Check if in enable mode. Return boolean."""
        debug = False
        self.write_channel('\n')
        output = self.read_until_prompt()
        if debug:
            print(output)
        return check_string in output

    def enable(self, cmd='', pattern='password', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        output = ""
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            self.write_channel(self.normalize_cmd(self.secret))
            output += self.read_until_prompt()
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode.")
        return output

    def exit_enable_mode(self, exit_command=''):
        """Exit enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(self, check_string='', pattern=''):
        """Checks if the device is in configuration mode or not."""
        debug = False
        if debug:
            print("pattern: {}".format(pattern))
        self.write_channel('\n')
        output = self.read_until_pattern(pattern=pattern)
        if debug:
            print("check_config_mode: {}".format(repr(output)))
        return check_string in output

    def config_mode(self, config_command='', pattern=''):
        """Enter into config_mode."""
        output = ''
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_config_mode(self, exit_config='', pattern=''):
        """Exit from configuration mode."""
        debug = False
        output = ''
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            output = self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        if debug:
            print("exit_config_mode: {}".format(output))
        return output

    def send_config_from_file(self, config_file=None, **kwargs):
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.
        """
        with io.open(config_file, encoding='utf-8') as cfg_file:
            return self.send_config_set(cfg_file, **kwargs)

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.
        """
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ''
        if not hasattr(config_commands, '__iter__'):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = self.config_mode()
        for cmd in config_commands:
            self.write_channel(self.normalize_cmd(cmd))
            time.sleep(delay_factor * .5)

        # Gather output
        output += self._read_channel_timing(delay_factor=delay_factor, max_loops=max_loops)
        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        if debug:
            print(output)
        return output

    @staticmethod
    def strip_ansi_escape_codes(string_buffer):
        """
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

        HP ProCurve's, Cisco SG300, and F5 LTM's require this (possible others)
        """
        debug = False
        if debug:
            print("In strip_ansi_escape_codes")
            print("repr = %s" % repr(string_buffer))

        code_position_cursor = chr(27) + r'\[\d+;\d+H'
        code_show_cursor = chr(27) + r'\[\?25h'
        code_next_line = chr(27) + r'E'
        code_erase_line = chr(27) + r'\[2K'
        code_erase_start_line = chr(27) + r'\[K'
        code_enable_scroll = chr(27) + r'\[\d+;\d+r'

        code_set = [code_position_cursor, code_show_cursor, code_erase_line, code_enable_scroll,
                    code_erase_start_line]

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
        """Any needed cleanup before closing connection."""
        pass

    def disconnect(self):
        """Gracefully close the SSH connection."""
        self.cleanup()
        if self.protocol == 'ssh':
            self.remote_conn_pre.close()
        elif self.protocol == 'telnet':
            self.remote_conn.close()

    def commit(self):
        """Commit method for platforms that support this."""
        raise AttributeError("Network device does not support 'commit()' method")


class TelnetConnection(BaseConnection):
    pass
