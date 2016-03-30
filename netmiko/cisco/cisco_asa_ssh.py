"""Subclass specific to Cisco ASA."""

from __future__ import unicode_literals
import re
from netmiko.ssh_connection import SSHConnection


class CiscoAsaSSH(SSHConnection):
    """Subclass specific to Cisco ASA."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal pager 0\n")

    def send_command(self, command_string, delay_factor=.1, max_loops=150,
                     strip_prompt=True, strip_command=True):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        output = super(CiscoAsaSSH, self).send_command(command_string, delay_factor,
                                                       max_loops, strip_prompt, strip_command)
        if "changeto" in command_string:
            self.set_base_prompt()
        return output

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
