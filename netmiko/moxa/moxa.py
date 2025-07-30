from netmiko.cisco_base_connection import CiscoSSHConnection


class MoxaBase(CiscoSSHConnection):
    """MOXA base driver"""

    pass


class MoxaSSH(MoxaBase):
    """MOXA SSH driver"""

    pass
