import re
import socket
import time

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoTimeoutException


class CiscoTpTCCE(CiscoSSHConnection):

    def __init__(self, ip='', host='', username='', password='', secret='', port=None,
                 device_type='', verbose=False, global_delay_factor=1, use_keys=False,
                 key_file=None, allow_agent=False, ssh_strict=False, system_host_keys=False,
                 alt_host_keys=False, alt_key_file='', ssh_config_file=None, timeout=8, line_feed='\n', shell_encoding='utf-8'):
        self.re_prompt_pattern = '[a-zA-Z]:\\\.*>'
        self.re_prompt_pattern = '^(OK|ERROR|Command not recognized\.)$'
        self.prompt_search_last_depth = -2
        CiscoSSHConnection.__init__(self, ip=ip, host=host, username=username, password=password, secret=secret, port=port,
                 device_type=device_type, verbose=verbose, global_delay_factor=global_delay_factor, use_keys=use_keys,
                 key_file=key_file, allow_agent=allow_agent, ssh_strict=ssh_strict, system_host_keys=system_host_keys,
                 alt_host_keys=alt_host_keys, alt_key_file=alt_key_file, ssh_config_file=ssh_config_file, timeout=timeout, line_feed=line_feed, shell_encoding=shell_encoding)
                 
    def disable_paging(self, *args, **kwargs):
        """Linux doesn't have paging by default."""
        return ""

    def set_base_prompt(self, pri_prompt_terminator='OK',
                        alt_prompt_terminator='ERROR', delay_factor=1):
        """Determine base prompt."""
        return super(CiscoSSHConnection, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)


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
        command_string = command_string.rstrip('\n')
        output_lines = output.split("\n")
        first_line = output_lines[0]
        if command_string in first_line:
            output_lines.pop(0)
            output = '\n'.join(output_lines)
        return output
