import re
import socket
import time

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoTimeoutException


class WindowsSSH(CiscoSSHConnection):

    def __init__(self, ip='', host='', username='', password='', secret='', port=None,
                 device_type='', verbose=False, global_delay_factor=1, use_keys=False,
                 key_file=None, allow_agent=False, ssh_strict=False, system_host_keys=False,
                 alt_host_keys=False, alt_key_file='', ssh_config_file=None, timeout=8, line_feed='\r\n', shell_encoding='cp850'):
        self.re_prompt_pattern = '[a-zA-Z]:\\\.*>'
        CiscoSSHConnection.__init__(self, ip=ip, host=host, username=username, password=password, secret=secret, port=port,
                 device_type=device_type, verbose=verbose, global_delay_factor=global_delay_factor, use_keys=use_keys,
                 key_file=key_file, allow_agent=allow_agent, ssh_strict=ssh_strict, system_host_keys=system_host_keys,
                 alt_host_keys=alt_host_keys, alt_key_file=alt_key_file, ssh_config_file=ssh_config_file, timeout=timeout, line_feed=line_feed, shell_encoding=shell_encoding)
                 
    def disable_paging(self, *args, **kwargs):
        """Linux doesn't have paging by default."""
        return ""

    def set_base_prompt(self, pri_prompt_terminator='>',
                        alt_prompt_terminator='>', delay_factor=1):
        """Determine base prompt."""
        return super(CiscoSSHConnection, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)

    def child_clean_channel(self, output):
        output = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('\r\n', output)
        return output

    def child_clean_output(self, output):
#        output = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('\r\n', output)
        return output

    def child_clean_prompt(self, output):
#        output = output.lstrip("\r\n")
#        output = output.lstrip("\n")
#        output += '>'   #parent class will remove last character (set_base_prompt method) so we added another one
        return output

    def _sanitize_output(self, output, strip_command=False, command_string=None,
                         strip_prompt=False):
        """Sanitize the output."""
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command and command_string:
            output = self.strip_command(self, command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)
        return output

    @staticmethod
    def strip_command(self, command_string, output):
        command_string = command_string.rstrip('\r\n')
        output_lines = output.split("\n")
        first_line = output_lines[1]
        if command_string in first_line:
            output_lines.pop(1)     #remove first lines from output to remove MS-DOS prompt and input command
            output = '\n'.join(output_lines)
        return output
