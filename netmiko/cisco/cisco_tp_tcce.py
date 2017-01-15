import re
import socket
import time

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.netmiko_globals import BACKSPACE_CHAR


class CiscoTpTcCeSSH(CiscoSSHConnection):

    def __init__(self, ip='', host='', username='', password='', secret='', port=None,
                 device_type='', verbose=False, global_delay_factor=1, use_keys=False,
                 key_file=None, allow_agent=False, ssh_strict=False, system_host_keys=False,
                 alt_host_keys=False, alt_key_file='', ssh_config_file=None, timeout=8):
        self.prompt_search_last_depth = -2
        CiscoSSHConnection.__init__(self, ip=ip, host=host, username=username, password=password, secret=secret, port=port,
                 device_type=device_type, verbose=verbose, global_delay_factor=global_delay_factor, use_keys=use_keys,
                 key_file=key_file, allow_agent=allow_agent, ssh_strict=ssh_strict, system_host_keys=system_host_keys,
                 alt_host_keys=alt_host_keys, alt_key_file=alt_key_file, ssh_config_file=ssh_config_file, timeout=timeout)
                 
    def disable_paging(self, *args, **kwargs):
        """Linux doesn't have paging by default."""
        return ""
        
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
        
        """self.set_base_prompt()"""
        self.disable_paging()
        self.set_terminal_width()        



    def set_base_prompt(self, pri_prompt_terminator='OK',
                        alt_prompt_terminator='ERROR', delay_factor=1):
        """Determine base prompt."""
        return super(CiscoSSHConnection, self).set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor)


        
    def send_command2(self, command_string, expect_string=None,
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
        if (hasattr(self, 'prompt_search_last_depth')):
            prompt_search_last_depth = self.prompt_search_last_depth
        else:
            prompt_search_last_depth = 0        
        
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
                    
                is_prompt_found = False
                j = -1
                if (prompt_search_last_depth != 0):
                    while (len(lines)>j*(-1)):
                        if debug:
                            print("searching on last line {0} of {1} : text= {2}".format(-1*j, -1*prompt_search_last_depth, lines[j]))
                        if re.search(search_pattern, lines[j].strip()):
                            is_prompt_found = True
                            break
                        if (j <= prompt_search_last_depth):
                            break
                        j = j - 1

                if (prompt_search_last_depth!=0 and is_prompt_found):
                   break
                elif re.search(search_pattern, output):
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

    def send_command(self, command_string, expect_string='^(OK|ERROR|Command not recognized\.)$',
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True):
        return self.send_command2(command_string=command_string, expect_string=expect_string,
                     delay_factor=delay_factor, max_loops=max_loops, auto_find_prompt=auto_find_prompt,
                     strip_prompt=strip_prompt, strip_command=strip_command)
