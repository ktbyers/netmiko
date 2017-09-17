from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class BrocadeNetironBase(CiscoSSHConnection):
    pass


class BrocadeNetironSSH(BrocadeNetironBase):
    pass


class BrocadeNetironTelnet(BrocadeNetironBase):
    def __init__(self, *args, **kwargs):
        super(BrocadeNetironTelnet, self).__init__(*args, **kwargs)
        self.RETURN = '\r\n'

    def telnet_login(self, pri_prompt_terminator='#', alt_prompt_terminator='>',
                     username_pattern=r"Username:", pwd_pattern=r"assword:",
                     delay_factor=1, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        super(BrocadeNetironTelnet, self).telnet_login(
              pri_prompt_terminator=pri_prompt_terminator,
              alt_prompt_terminator=alt_prompt_terminator,
              username_pattern=username_pattern,
              pwd_pattern=pwd_pattern,
              delay_factor=delay_factor,
              max_loops=max_loops)
