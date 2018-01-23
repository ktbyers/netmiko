"""
CiscoTpTcCeSSH Class
Class to manage Cisco Telepresence Endpoint on TC/CE software release. Also working for Cisco
Expressway/VCS

Written by Ahmad Barrin
"""
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoTpTcCeSSH(CiscoSSHConnection):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\r\n' if default_enter is None else default_enter
        super(CiscoTpTcCeSSH, self).__init__(*args, **kwargs)

    def disable_paging(self, *args, **kwargs):
        """Paging is disabled by default."""
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
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """Use 'OK' as base_prompt."""
        self.base_prompt = 'OK'
        return self.base_prompt

    def find_prompt(self, *args, **kwargs):
        """Use 'OK' as standard prompt."""
        return 'OK'

    def strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output."""
        expect_string = r'^(OK|ERROR|Command not recognized\.)$'
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        if re.search(expect_string, last_line):
            return self.RESPONSE_RETURN.join(response_list[:-1])
        else:
            return a_string

    def send_command(self, *args, **kwargs):
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
        if len(args) >= 2:
            expect_string = args[1]
        else:
            expect_string = kwargs.get('expect_string')
            if expect_string is None:
                expect_string = r'(OK|ERROR|Command not recognized\.)'
                expect_string = self.RETURN + expect_string + self.RETURN
                kwargs.setdefault('expect_string', expect_string)

        output = super(CiscoSSHConnection, self).send_command(*args, **kwargs)
        return output

    def save_config(self):
        """Not Implemented"""
        raise NotImplementedError
