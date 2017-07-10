from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.netmiko_globals import BACKSPACE_CHAR


class BrocadeFastironTelnet(CiscoBaseConnection):
    """Brocade FastIron aka ICX support."""
    def session_preparation(self):
        self.protocol = 'telnet'
        """FastIron requires to be enable mode to disable paging."""
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="skip-page-display")

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n\r\n', '\r\r\n','\r\n', '\n\r' to '\n."""
        newline = re.compile(r'(\r\n\r\n|\r\r\n|\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"Username:", pwd_pattern=r"assword:",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        super(BrocadeFastironTelnet, self).telnet_login(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                username_pattern=username_pattern,
                pwd_pattern=pwd_pattern,
                delay_factor=delay_factor,
                max_loops=max_loops)

    def _test_channel_read(self, count=40, pattern=""):
        """Try to read the channel (generally post login) verify you receive data back."""

        def _increment_delay(main_delay, increment=1.1, maximum=8):
            """Increment sleep time to a maximum value."""
            main_delay = main_delay * increment
            if main_delay >= maximum:
                main_delay = maximum
            return main_delay

        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)
        main_delay = delay_factor * .1
        time.sleep(main_delay * 10)
        new_data = ""
        while i <= count:
            new_data += self._read_channel_timing()
            if new_data and pattern:
                if re.search(pattern, new_data):
                    break
            elif new_data:
                break
            else:
                """Must send \r\n for ICX"""
                self.write_channel('\r\n')

            main_delay = _increment_delay(main_delay)
            time.sleep(main_delay)
            i += 1

        # check if data was ever present
        if new_data:
            return ""
        else:
            raise NetMikoTimeoutException("Timed out waiting for data")

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only."""
        debug = False
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        """Must send \r\n for ICX"""
        self.write_channel("\r\n")
        time.sleep(delay_factor * .1)

        # Initial attempt to get prompt
        prompt = self.read_channel()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        if debug:
            print("prompt1: {}".format(prompt))

        # Check if the only thing you received was a newline
        count = 0
        prompt = prompt.strip()
        while count <= 10 and not prompt:
            prompt = self.read_channel().strip()
            if prompt:
                if debug:
                    print("prompt2a: {}".format(repr(prompt)))
                    print("prompt2b: {}".format(prompt))
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt).strip()
            else:
                """Must send \r\n for ICX"""
                self.write_channel("\r\n")
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

    @staticmethod
    def normalize_cmd(command):
        """Normalize CLI commands to have a single trailing newline."""
        command = command.rstrip("\n")
        """Must send \r\n for ICX"""
        command += '\r\n'
        return command

    def check_enable_mode(self, check_string=''):
        """Check if in enable mode. Return boolean."""
        debug = False
        """Must send \r\n for ICX"""
        self.write_channel('\r\n')
        output = self.read_until_prompt()
        if debug:
            print(output)
        return check_string in output

    def check_config_mode(self, check_string=')#', pattern=''):
        """Checks if the device is in configuration mode or not."""
        debug = False
        if not pattern:
            pattern = re.escape(self.base_prompt)
        if debug:
            print("pattern: {}".format(pattern))
        """Must send \r\n for ICX"""
        self.write_channel('\r\n')
        output = self.read_until_pattern(pattern=pattern)
        if debug:
            print("check_config_mode: {}".format(repr(output)))
        return check_string in output

    def config_mode(self, config_command='config term', pattern=''):
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super(CiscoBaseConnection, self).config_mode(config_command=config_command,
                                                            pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern=''):
        """Exit from configuration mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        return super(CiscoBaseConnection, self).exit_config_mode(exit_config=exit_config,
                                                                 pattern=pattern)

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str
        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_str: str
        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int
        :param max_loops: Controls wait time in conjunction with delay_factor (default: 150).
        :type max_loops: int
        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool
        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool
        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(delay_factor * .2)
        self.clear_buffer()
        self.write_channel(command_string)

        # Keep reading data until search_pattern is found (or max_loops)
        i = 1
        output = ''
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                output += new_data
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
                                       command_string=command_string[:-1], strip_prompt=strip_prompt)
        return output

