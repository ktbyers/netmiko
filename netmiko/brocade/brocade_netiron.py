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
