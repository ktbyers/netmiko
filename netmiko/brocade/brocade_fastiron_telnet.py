from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoBaseConnection


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
    
    def check_enable_mode(self, check_string=''):
        """Check if in enable mode. Return boolean."""
        debug = False
        """Must send \r\n for CER"""
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
