"""
Tested with

EDS-508A
EDS-516A

Note:
This only works in CLI mode. If the device is in Menu mode, you need to change that first.
"""

from netmiko.cisco_base_connection import CiscoSSHConnection


class MoxaNosBase(CiscoSSHConnection):
    """MOXA base driver"""

    pass


class MoxaNosSSH(MoxaNosBase):
    """MOXA SSH driver"""

    pass
