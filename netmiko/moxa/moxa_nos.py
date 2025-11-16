from netmiko.cisco_base_connection import CiscoSSHConnection


class MoxaNosBase(CiscoSSHConnection):
    """MOXA base driver"""

    pass


class MoxaNosSSH(MoxaNosBase):
    """MOXA SSH driver"""

    pass
