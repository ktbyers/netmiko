from __future__ import unicode_literals
from netmiko.vyos.vyos_ssh import VyOSSSH


class UbiquitiEdgeSSH(VyOSSSH):
    """
    Implements support for Ubiquity EdgeOS devices.

    Mostly identical to VyOS (same root OS of Vyatta) inheriting from there.
    """
    pass