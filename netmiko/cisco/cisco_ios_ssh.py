from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.base_connection import TelnetConnection


class CiscoIosSSH(CiscoSSHConnection):
    pass


class CiscoIosTelnet(TelnetConnection):
    pass
