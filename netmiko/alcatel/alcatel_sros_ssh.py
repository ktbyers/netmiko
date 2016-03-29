"""Alcatel-Lucent SROS support."""
import re
from netmiko.ssh_connection import SSHConnection


class AlcatelSrosSSH(SSHConnection):
    """Alcatel-Lucent SROS support."""
    def session_preparation(self):
        self.set_base_prompt()
        self.disable_paging(command="environment no more\n")

    def set_base_prompt(self, *args, **kwargs):
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super(AlcatelSrosSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)(>.*)*#', cur_base_prompt)
        if match:
            # strip off >... from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def enable(self, *args, **kwargs):
        pass

    def config_mode(self, *args, **kwargs):
        pass
