"""Dell EMC Networking OS10 Driver - supports dellos10."""

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.linux.linux_ssh import LinuxFileTransfer


class DellOS10SSH(CiscoSSHConnection):
    """Dell EMC Networking OS10 Driver - supports dellos10."""
    pass


class DellOS10FileTransfer(LinuxFileTransfer):
    """Dell EMC Networking OS10 SCP File Transfer driver."""
    pass
