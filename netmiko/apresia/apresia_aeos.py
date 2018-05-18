from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.netmiko_globals import BACKSPACE_CHAR
from netmiko.utilities import get_structured_data


class ApresiaAeosBase(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command="", delay_factor=1):
        """No disable paging command mode on AEOS"""
        pass

    def set_terminal_width(self, command="", delay_factor=1):
        """No terminal width command mode on AEOS"""
        pass

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True,
                     use_textfsm=False):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.
        :param command_string: The command to be executed on the remote device.
        :type command_string: str
        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_string: str
        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int
        :param max_loops: Controls wait time in conjunction with delay_factor. Will default to be
            based upon self.timeout.
        :type max_loops: int
        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool
        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool
        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool
        :param use_textfsm: Process command output through TextFSM template (default: False).
        :type normalize: bool
        """
        # Time to delay in each read loop
        loop_delay = .2

        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # and delay_factor arguments for backwards compatibility).
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor == 1 and max_loops == 500:
            # Default arguments are being used; use self.timeout instead
            max_loops = int(self.timeout / loop_delay)

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

        time.sleep(delay_factor * loop_delay)
        self.clear_buffer()
        self.write_channel(command_string)

        i = 1
        output = ''
        # Keep reading data until search_pattern is found or until max_loops is reached.
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                if re.search('--- more ---', new_data):
                    self.write_channel(' ')
                output += new_data
                try:
                    lines = output.split(self.RETURN)
                    first_line = lines[0]
                    # First line is the echo line containing the command. In certain situations
                    # it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re.sub(pattern, repl='', string=first_line)
                        lines[0] = first_line
                        output = self.RETURN.join(lines)
                except IndexError:
                    pass
                if re.search(search_pattern, output):
                    break
            else:
                time.sleep(delay_factor * loop_delay)
            i += 1
        else:   # nobreak
            raise IOError("Search pattern never detected in send_command_expect: {}".format(
                search_pattern))

        output = self._sanitize_output(output, strip_command=strip_command,
                                       command_string=command_string, strip_prompt=strip_prompt)

        output = self._strip_paging(output)

        if use_textfsm:
            output = get_structured_data(output, platform=self.device_type,
                                         command=command_string.strip())
        return output

    def _strip_paging(self, output):
        return re.sub(r'\n--- more ---\n\s+\n', '', output)


class ApresiaAeosSSH(ApresiaAeosBase):
    pass


class ApresiaAeosTelnet(ApresiaAeosBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\r\n' if default_enter is None else default_enter
        super(ApresiaAeosTelnet, self).__init__(*args, **kwargs)
