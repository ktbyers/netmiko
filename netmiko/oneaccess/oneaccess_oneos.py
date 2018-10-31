"""OneAccess ONEOS support."""
from __future__ import print_function
from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.base_connection import BaseConnection


class OneaccessOneosSSH(CiscoSSHConnection):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super(OneaccessOneosSSH, self).__init__(*args, **kwargs)

class OneaccessOneosTelnet(BaseConnection):
    pass

