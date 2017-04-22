"""Subclass specific to Cisco ASA."""

from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class CiscoAsaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco ASA."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        if self.secret:
            self.enable()
        else:
            self.asa_login()
        self.disable_paging(command="terminal pager 0\n")
        self.set_terminal_width(command="terminal width 511\n")

    def send_command_timing(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        output = super(CiscoAsaSSH, self).send_command_timing(*args, **kwargs)
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs['command_string']
        if "changeto" in command_string:
            self.set_base_prompt()
        return output

    def send_command(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs['command_string']

        # If changeto in command, look for '#' to determine command is done
        if "changeto" in command_string:
            if len(args) <= 1:
                expect_string = kwargs.get('expect_string', '#')
                kwargs['expect_string'] = expect_string
        output = super(CiscoAsaSSH, self).send_command(*args, **kwargs)

        if "changeto" in command_string:
            self.set_base_prompt()

        return output

    def send_command_expect(self, *args, **kwargs):
        """Backwards compaitibility."""
        return self.send_command(*args, **kwargs)

    def set_base_prompt(self, *args, **kwargs):
        """
        Cisco ASA in multi-context mode needs to have the base prompt updated
        (if you switch contexts i.e. 'changeto')

        This switch of ASA contexts can occur in configuration mode. If this
        happens the trailing '(config*' needs stripped off.
        """
        cur_base_prompt = super(CiscoAsaSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)\(conf.*', cur_base_prompt)
        if match:
            # strip off (conf.* from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def asa_login(self):
        """
        Handle ASA reaching privilege level 15 using login

        twb-dc-fw1> login
        Username: admin
        Password: ************
        """
        delay_factor = self.select_delay_factor(0)

        i = 1
        max_attempts = 50
        self.write_channel("login\n")
        while i <= max_attempts:
            time.sleep(.5 * delay_factor)
            output = self.read_channel()
            if 'sername' in output:
                self.write_channel(self.username + '\n')
            elif 'ssword' in output:
                self.write_channel(self.password + '\n')
            elif '#' in output:
                break
            else:
                self.write_channel("login\n")
            i += 1
